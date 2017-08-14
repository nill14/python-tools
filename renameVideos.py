#!/bin/python3
import argparse

from pathlib import Path
import os
import exiftool


def main():
    args = parseArgs()
    path = args.path
    if args.verbose > 0:
        print("Using dir %s" % path)

    videos = findVideos(args, path)
    if args.verbose > 2:
        print("Found videos: %s" % (videos))

    metadata = exifTitles(args, videos)
    tuples = collectData(args, metadata)
    renameProcess(args, tuples)


#     print(list(map(lambda x: exifTitle(args, x), videos)))


def findVideos(args, path):
    videos = path.glob(args.glob)
    return [str(v) for v in videos]


def parseArgs():
    parser = argparse.ArgumentParser(
        description="Convert Video Names")
    parser.add_argument('path', default=Path(), type=Path,
                        nargs='?', help="Directory with videos or '.' by default.")
    parser.add_argument('-v', "--verbose", action="count", default=0,
                        help='Print some extra information. (-v -vv -vvv) is supported.')
    parser.add_argument("--glob", default="**/*.mp4",
                        help="Glob to search videos, by default '**/*.mp4'.")
    parser.add_argument('-i', "--interactive", action="store_true",
                        help='Confirm each rename operation.')
    parser.add_argument('-n', "--dry-run", action="store_true", dest='dryRun',
                        help='Print the information but do not rename anything.')
    return parser.parse_args()


def exifTitles(args, files):
    """title=$(exiftool -s -s -s -Title "$ff");"""
    if len(files) > 0:
        with exiftool.ExifTool() as et:
            return et.get_metadata_batch(files)

    return []


class Element:
    def __init__(self, path):
        self.path = path


def collectData(args, metadata):
    for data in metadata:
        newPath = None
        title = data.get("QuickTime:Title")
        sourceFile = data["SourceFile"]
        path = Path(sourceFile)
        if (title is not None):
            name, ext = os.path.splitext(path.name)
            escaped = escTitle(args, title)
            newPath = Path(path.parent, escaped + ext)

        yield (title, data, path, newPath)


def renameProcess(args, tuples):
    for title, data, path, newPath in tuples:
        if title is None:
            if args.verbose > 1:
                print("Skipping '%s' (no title)" % path)
                if args.verbose > 2:
                    for item in data.items():
                        print("%60s : %s" % item)

        elif path == newPath:
            if args.verbose > 1:
                print("Skipping '%s' (already renamed)" % path)

        elif newPath is not None:
            if args.interactive:
                x = ''
                while x not in ['y', 'n']:
                    x = input("Rename '%s' to '%s'? [Yn]:" % (
                        path, newPath)).lower()

                if x == 'y' and not args.dryRun:
                    path.rename(newPath)
            else:
                print("%60s -> %s" % (path, newPath))
                if not args.dryRun:
                    path.rename(newPath)

        else:
            raise Exception(
                "Unexpected - can't rename to None - stop here rather than eat your data")


def escTitle(args, title):
    replaces = {'?': '_',
                ':': '_',
                '&': '_',
                '!': '_',
                '"': '',
                '“': '',
                '”': ''}
    val = ''.join(map(lambda ch: replaces.get(ch, ch), title))
    if args.verbose > 2:
        print("escTitle(%s) = '%s'" % (title, val))
    return val


if __name__ == "__main__":
    main()
