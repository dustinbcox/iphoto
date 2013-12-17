#!/usr/bin/env python
"""
OS X iPhoto Database Support
Copyright (C) 2013 Dustin B. Cox <dustin@dustinbcox.com>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import argparse
import datetime
import plistlib
import pprint
import os


def convert_timer_interval(seconds):
    """ Method to convert a timer interval into a python datetime """
    # Referenced:
    # http://www.tablix.org/~avian/blog/archives/2011/02/to_mac_and_back_again/
    return datetime.datetime(2001, 1, 1) + datetime.timedelta(seconds=seconds)


class IPhoto(object):
    """ OS X iPhoto support """
    def __init__(self, iphoto_library='~/Pictures/iPhoto Library.photolibrary',
                 albumdata_filename='AlbumData.xml'):
        """ Open AlbumData.xml and generate internal data """
        if iphoto_library.startswith("~/"):
            iphoto_library = os.path.join(os.environ["HOME"],
                                          iphoto_library[2:])
        self._albumdata_fullpath = os.path.join(iphoto_library,
                                                albumdata_filename)
        self._images = {}
        self._albums = {}

        database = plistlib.readPlist(self._albumdata_fullpath)

        # All images (and movies) are referenced here:
        master_image_list = database['Master Image List']
        for image_id in master_image_list:
            self._images[image_id] = \
                self._rewrite_date_fields(master_image_list[image_id])

        # { AlbumName: { 'photos': ["image_id", "image_id"], }
        for album in database['List of Albums']:
            if album['PhotoCount'] != len(album['KeyList']):
                raise ValueError("Error: PhotoCount != length KeyList array")
            self._albums[album['AlbumName']] = {'photos': album['KeyList'],
                                                'count': album['PhotoCount'],
                                                'id': album['AlbumId']}

    def _rewrite_date_fields(self, photo_data):
        """ Internal method to convert AsTimerInterval into python datetimes,
        the photo_data dict with keynames "XYZAsTimerInterval" will be saved
        just as XYZ.

        { 'image_id': {'Caption': 'filename_without_ext_usually',
                        'Comment': ' ',
                        'DateAsTimerInterval': seconds.0,
                        'DateAsTimerIntervalGMT': seconds.0,
                        'GUID': 'base64',
                        'ImagePath': 'local_filepath_to_image',
                        'MediaType': 'Image',
                        'MetaModDateAsTimerInterval': seconds.1234,
                        'ModDateAsTimerInterval': seconds.4567,
                        'Rating': 0,
                        'Roll': 55,
                        'ThumbPath': 'local_filepath_to_thumb'},

        Internally it will converted self._images{} for each image:
         { 'image_id': {'Caption': 'filename_without_ext_usually',
                        'Comment': ' ',
                        'Date': datetime.datetime(),
                        'DateGMT': datetime.datetime(),
                        'GUID': 'base64',
                        'ImagePath': 'local_filepath_to_image',
                        'MediaType': 'Image',
                        'MetaModDate': datetime.datetime(),
                        'ModDate': datetime.datetime(),
                        'Rating': 0,
                        'Roll': 55,
                        'ThumbPath': 'local_filepath_to_thumb'},


        """
        for old_key, new_key in (('ModDateAsTimerInterval', 'ModDate'),
                                 ('DateAsTimerInterval', 'Date'),
                                 ('MetaModDateAsTimerInterval', 'MetaModDate'),
                                 ('DateAsTimerIntervalGMT', 'DateGMT')):
            if old_key in photo_data:
                photo_data[new_key] = \
                    convert_timer_interval(photo_data[old_key])
                del photo_data[old_key]
        return photo_data

    def albums(self):
        """ Iterate over album names """
        for album in self._albums:
            yield album

    def album_data(self, album_name):
        """  Album data (dict) given album_name:
            {'photos': [ image_id,...], 'count': 1234, 'id': 2}
        """
        return self._albums[album_name]

    def photos(self, album, include_raw_photos=False):
        """ Return photos from album:
            {'Caption': 'filename_without_ext_usually',
                        'Comment': ' ',
                        'Date': datetime.datetime(),
                        'DateGMT': datetime.datetime(),
                        'GUID': 'base64',
                        'ImagePath': 'local_filepath_to_image',
                        'MediaType': 'Image',
                        'MetaModDate': datetime.datetime(),
                        'ModDate': datetime.datetime(),
                        'Rating': 0,
                        'Roll': 55,
                        'ThumbPath': 'local_filepath_to_thumb'},
        """
        for photo in self.album_data(album)['photos']:
            # OriginalPath seems to be set on "RAW" photos
            if "OriginalPath" in photo and include_raw_photos is False:
                continue
            yield self._images[photo]


def main():
    """ Main entry point, if called directly """
    parser = argparse.ArgumentParser(description="iPhoto library")
    parser.add_argument('-a', '--album', nargs='+',
                        help='Select only specific album(s)')
    parser.add_argument('-l', '--list', action='store_true',
                        help="List albums")
    args = parser.parse_args()

    iphoto = IPhoto()
    if args.album:
        for album_name in args.album:
            for photos in iphoto.photos(album_name):
                pprint.PrettyPrinter().pprint(photos)
    elif args.list:
        for albums in iphoto.albums():
            print albums
    else:
        parser.print_usage()


if __name__ == "__main__":
    main()
