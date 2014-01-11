"""Unit testing for IPhoto"""

import unittest
import iphoto
from datetime import datetime
from mock import patch


MOCK_DATABASE = {'List of Albums': [{'AlbumId': '1',
                                     'AlbumName': 'album1',
                                     'KeyList': ['1', '2'],
                                     'PhotoCount': 2}],
                 'Master Image List': {'1':{'Caption': 'A normal caption',
                                            'Comment': 'no comment',
                                            'GUID': '234134234341234123411234',
                                            'ImagePath': 'bad/joke.jpg',
                                            'MediaType': 'Image',
                                            'Rating': 0.0,
                                            'ThumbPath': 'bad/joke_thumb.jpg'},
                                       '2':{'Caption': 'Another caption',
                                            'Comment': 'Another no comment',
                                            'GUID': '234634576344565634563456',
                                            'ImagePath': 'nowhere/obe.png',
                                            'MediaType': 'Image',
                                            'Rating': 50.0,
                                            'ThumbPath': 'nohre/toiny.png'}}}


class TestIPhoto(unittest.TestCase):
    """Unit testing for IPhoto"""
    @patch.object(iphoto.plistlib, 'readPlist')
    def setUp(self, mock):
        """ initialize self.iphoto with MOCK_DATABASE"""
        mock.return_value = MOCK_DATABASE
        self.iphoto = iphoto.IPhoto()
    def test_convert_timer_interval(self):
        """ Unit testing for convert_timer_interval """
        self.assertEqual(datetime(2013, 12, 19, 0, 46, 12, 656490),
                        iphoto.convert_timer_interval(409106772.65649))
    def test_timerinterval_to_datetime(self):
        """ Test convert_timer_interval """
        sample = { 'DateAsTimerInterval': 360962921.0,
                   'DateAsTimerIntervalGMT': 360948521.0,
                   'MetaModDateAsTimerInterval': 409536614.113663,
                   'ModDateAsTimerInterval': 377914153.0,
        }
        expected = { 'Date': datetime(2012, 6, 9, 19, 28, 41),
                     'DateGMT': datetime(2012, 6, 9, 15, 28, 41),
                     'MetaModDate': datetime(2013, 12, 24, 0, 10, 14, 113663),
                     'ModDate': datetime(2012, 12, 23, 0, 9, 13)
        }
        self.assertDictEqual(expected, iphoto.timerinterval_to_datetime(sample))
    def test_photos(self):
        """ Test database """
        photos = list(self.iphoto.photos('album1'))
        self.assertEqual(len(photos), len(MOCK_DATABASE['Master Image List']))
        self.assertEqual(photos[0]['Comment'],
                         MOCK_DATABASE['Master Image List']['1']['Comment'])
    def test_albums(self):
        """ Test albums """
        albums = list(self.iphoto.albums())
        self.assertEqual(len(albums), len(MOCK_DATABASE['List of Albums']))

    def test_album_data(self):
        """ Test album_data """
        album_data = {'photos': MOCK_DATABASE['List of Albums'][0]['KeyList'],
                      'count': MOCK_DATABASE['List of Albums'][0]['PhotoCount'],
                      'id': MOCK_DATABASE['List of Albums'][0]['AlbumId']}
        self.assertEqual(self.iphoto.album_data('album1'), album_data)
