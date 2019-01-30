import unittest
import mock


class SuperSlackerTests(unittest.TestCase):
    token = 'testtokentesttokentesttoken'
    channel = ('#testchannel')
    unexpected_err_msg = 'server;bar:foo;BACKOFF;PROCESS_STATE_FATAL'
    events = 'FATAL,EXITED'
    hostname = 'server'

    def _get_target_class(self):
        from superslacker.superslacker import SuperSlacker
        return SuperSlacker

    def _make_one_mocked(self, **kwargs):
        kwargs['token'] = kwargs.get('token', self.token)
        kwargs['channel'] = kwargs.get('channel', self.channel)
        kwargs['events'] = kwargs.get('events', self.events)
        kwargs['hostname'] = kwargs.get('hostname', self.hostname)

        obj = self._get_target_class()(**kwargs)
        obj.send_message = mock.Mock()
        return obj

    def get_process_fatal_event(self, pname, gname):
        headers = {
            'ver': '3.0', 'poolserial': '7', 'len': '71',
            'server': 'supervisor', 'eventname': 'PROCESS_STATE_FATAL',
            'serial': '7', 'pool': 'superslacker',
        }
        payload = 'processname:{} groupname:{} from_state:BACKOFF'.format(pname, gname)
        return (headers, payload)

    def test_get_process_state_change_msg(self):
        crash = self._make_one_mocked()
        hdrs, payload = self.get_process_fatal_event('foo', 'bar')
        msg = crash.get_process_state_change_msg(hdrs, payload)
        self.assertEquals(self.unexpected_err_msg, msg)

if __name__ == '__main__':
    unittest.main()
