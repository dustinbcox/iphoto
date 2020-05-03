#!/usr/bin/env python
""" iPhoto Database Support """

# OS X iPhoto Database Support
# Copyright (C) 2013 Dustin B. Cox <dustin@dustinbcox.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import argparse
import datetime
import plistlib
import pprint
import os
import json
import sys


def convert_timer_interval(seconds):
    """Method to convert a timer interval into a python datetime

    Args:
        seconds (int): Number of seconds in for mac epoch

    Returns:
        datetime.datetime()

    """
    # Referenced:
    # http://www.tablix.org/~avian/blog/archives/2011/02/to_mac_and_back_again/
    return datetime.datetime(2001, 1, 1) + datetime.timedelta(seconds=seconds)


def timerinterval_to_datetime(data):
    """Convert all fields with AsTimerInterval into python datetimes.

    Args:
        data (dict): A dictionary that should look something like this::

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
                           'ThumbPath': 'local_filepath_to_thumb'}, ...}

    Returns:
        dict. ::

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
                           'ThumbPath': 'local_filepath_to_thumb'}, ...}

    """
    for key in data:
        if 'AsTimerInterval' in key:
            new_key = key.replace('AsTimerInterval', '')
            data[new_key] = convert_timer_interval(data[key])
            del data[key]
    return data


class IPhoto(object):
    """ OS X iPhoto support """
    def __init__(self, iphoto_library='~/Pictures/iPhoto Library.photolibrary',
                 albumdata_filename='AlbumData.xml'):
        """ Open AlbumData.xml and generate internal data

        Args:
            iphoto_library (str): Path to the iPhoto Library.photolibrary dir
            albumdata_filename (str): filename of AlbumData.xml

        """
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
                timerinterval_to_datetime(master_image_list[image_id])

        # { AlbumName: { 'photos': ["image_id", "image_id"], }
        for album in database['List of Albums']:
            if album['PhotoCount'] != len(album['KeyList']):
                raise ValueError("Error: PhotoCount != length KeyList array")
            self._albums[album['AlbumName']] = {'photos': album['KeyList'],
                                                'count': album['PhotoCount'],
                                                'id': album['AlbumId']}

    def albums(self):
        """ Generator for album names

        Returns:
            generator of str for each album name

        """
        for album in self._albums:
            yield album

    def album_data(self, album_name):
        """ Album data for album_name

        Args:
            album_name(str): The actual album name

        Returns:
            dict. With the album details::

                {'photos': [ image_id,...], 'count': 1234, 'id': 2}

        """
        return self._albums[album_name]

    def photos(self, album, include_raw_photos=False):
        """ Generator for photos given an album_name:

            Args:
                album (str): album name
                include_raw_photos (bool): if True include photos that are RAW

            Returns:
                generator of dicts With these keys ::

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
                     'ThumbPath': 'local_filepath_to_thumb'}

        """
        for photo in self.album_data(album)['photos']:
            # OriginalPath seems to be set on "RAW" photos
            if "OriginalPath" in photo and include_raw_photos is False:
                continue
            yield self._images[photo]


class DatetimeEncoder(json.JSONEncoder):
    """ Handle Python datetime when converting to JSON """
    # Source: http://stackoverflow.com/questions/8011081/ \
    #         cannot-serialize-datetime-as-json-from-cherrypy
    def default(self, obj):
        """ Override the default handler and if a given object has a callable
            isoformat then call it to ensure datetime or date's are converted.

            This is required because the json module doesn't support datetime

            Args:
                obj (obj): Current object

            Returns:
                string

        """
        if hasattr(obj, 'isoformat'):
            return obj.isoformat()
        else:
            return json.JSONEncoder.default(self, obj)


def main():
    """ Main entry point, if called directly """
    parser = argparse.ArgumentParser(description="iPhoto library")
    parser.add_argument('-a', '--album', nargs='+',
                        help='Select only specific album(s)')
    parser.add_argument('-l', '--list', action='store_true',
                        help="List albums")
    parser.add_argument('-f', '--format', choices=['text', 'json'],
                        default='text',
                        help='Output format type. The default is text')
    args = parser.parse_args()
    iphoto = IPhoto()
    if args.album:
        if args.format == 'json':
            output = {}
            for album_name in args.album:
                output[album_name] = list(iphoto.photos(album_name))
            json.dump(output, sys.stdout, indent=2, cls=DatetimeEncoder)
        elif args.format == 'text':
            pprinter = pprint.PrettyPrinter(indent=2)
            for album in args.album:
                for photo in iphoto.photos(album):
                    print(("--[ Album: {0} : Photo {1} ] ----------------".
                          format(album, photo['GUID'])))
                    pprinter.pprint(photo)
    elif args.list:
        output = sorted(list(iphoto.albums()))
        if args.format == 'json':
            json.dump(output, sys.stdout, indent=2)
        elif args.format == 'text':
            for album in output:
                print(album)
    else:
        parser.print_usage()

if __name__ == "__main__":
    main()
