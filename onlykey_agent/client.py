"""
Connection to hardware authentication device.

It is used for getting SSH public keys and ECDSA signing of server requests.
"""
import binascii
import io
import logging
import re
import hashlib

from onlykey import OnlyKey, Message

from . import formats, util
import ed25519
import time

log = logging.getLogger(__name__)


class Client(object):
    """Client wrapper for SSH authentication device."""

    def __init__(self, curve=formats.CURVE_ED25519, slot='1'):
        """Connect to hardware device."""
        self.device_name = 'OnlyKey'
        self.ok = OnlyKey()
        # TODO(tsileo): hard-code the curve and remove/disable the CLI args
        self.curve = curve
        self.slot = int('1%02d' % int(slot))  # Will rebuilt the slot ID, like 101 for slot 1

    def __enter__(self):
        """Start a session, and test connection."""
        self.ok.read_string(timeout_ms=50)
        empty = 'a'
        while not empty:
            empty = self.ok.read_string(timeout_ms=50)
        return self

    def __exit__(self, *args):
        """Forget PIN, shutdown screen and disconnect."""
        log.info('disconnected from %s', self.device_name)
        self.ok.close()

    def get_identity(self, label, index=0):
        """Parse label string into Identity protobuf."""
        identity = string_to_identity(label)
        identity['proto'] = 'ssh'
        identity['index'] = index
        print 'identity', identity
        return identity

    def get_public_key(self, label):
        """Get SSH public key corresponding to specified by label."""
        log.info('getting public key (%s) from %s...',
                 self.curve, self.device_name)

        self.ok.send_message(msg=Message.OKGETPUBKEY, payload=chr(self.slot))
        time.sleep(1)

        # self.ok.send_message(msg=Message.OKGETSSHPUBKEY)

        vk = ed25519.VerifyingKey(self.ok.read_bytes(32, to_str=True))

        return formats.export_public_key(vk=vk, label=label)

    def sign_ssh_challenge(self, label, blob):
        """Sign given blob using a private key, specified by the label."""
        msg = _parse_ssh_blob(blob)
        log.debug('%s: user %r via %r (%r)',
                  msg['conn'], msg['user'], msg['auth'], msg['key_type'])
        log.debug('nonce: %s', binascii.hexlify(msg['nonce']))
        log.debug('fingerprint: %s', msg['public_key']['fingerprint'])
        log.debug('hidden challenge size: %d bytes', len(blob))

        # self.ok.send_large_message(payload=blob, msg=Message.OKSIGNSSHCHALLENGE)
        log.info('please confirm user "%s" login to "%s" using %s',
                 msg['user'], label, self.device_name)


        test_payload = blob
        # Compute the challenge pin
        h = hashlib.sha256()
        h.update(test_payload)
        d = h.digest()

        assert len(d) == 32

        def get_button(byte):
            ibyte = ord(byte)
            if ibyte < 6:
                return 1
            return ibyte % 5 + 1

        b1, b2, b3 = get_button(d[0]), get_button(d[15]), get_button(d[31])

        self.ok.send_large_message2(msg=Message.OKSIGNCHALLENGE, payload=test_payload, slot_id=self.slot)


        log.info('Please enter the 3 digit challenge code on OnlyKey (and press ENTER if necessary)')
        print '{} {} {}'.format(b1, b2, b3)
        raw_input()
        for _ in xrange(50):
            result = self.ok.read_string(timeout_ms=250)
            log.debug('result from device = %s', result)
            if len(result) == 64:
                return result

        raise Exception('failed to sign challenge')

_identity_regexp = re.compile(''.join([
    '^'
    r'(?:(?P<proto>.*)://)?',
    r'(?:(?P<user>.*)@)?',
    r'(?P<host>.*?)',
    r'(?::(?P<port>\w*))?',
    r'(?P<path>/.*)?',
    '$'
]))


def string_to_identity(s, identity_type=dict):
    """Parse string into Identity protobuf."""
    m = _identity_regexp.match(s)
    result = m.groupdict()
    log.debug('parsed identity: %s', result)
    kwargs = {k: v for k, v in result.items() if v}
    return identity_type(**kwargs)


def _parse_ssh_blob(data):
    res = {}
    i = io.BytesIO(data)
    res['nonce'] = util.read_frame(i)
    i.read(1)  # SSH2_MSG_USERAUTH_REQUEST == 50 (from ssh2.h, line 108)
    res['user'] = util.read_frame(i)
    res['conn'] = util.read_frame(i)
    res['auth'] = util.read_frame(i)
    i.read(1)  # have_sig == 1 (from sshconnect2.c, line 1056)
    res['key_type'] = util.read_frame(i)
    public_key = util.read_frame(i)
    res['public_key'] = formats.parse_pubkey(public_key)
    assert not i.read()
    return res
