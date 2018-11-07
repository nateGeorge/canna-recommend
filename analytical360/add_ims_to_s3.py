import boto
from boto.s3.connection import S3Connection, Location
import os
import glob
import math
from filechunkio import FileChunkIO

class awsS3(object):
    def __init__(self, bucket_name='mistress-pics'):
        # set env variable AWS_CREDENTIAL_FILE
        # http://stackoverflow.com/questions/5396932/why-are-no-amazon-s3-authentication-handlers-ready
        self.conn = boto.connect_s3()
        self.bucket = self.conn.get_bucket(bucket_name)
        bucket_location = self.bucket.get_location()
        if bucket_location: # fix from https://github.com/boto/boto/issues/2207#issuecomment-60682869
            self.conn = boto.s3.connect_to_region(bucket_location)
            self.bucket = self.conn.get_bucket(bucket_name)

    def upload_big_file(self, source_path, verbose=True):
        source_size = os.path.getsize(source_path)
        mp = self.bucket.initiate_multipart_upload(os.path.basename(source_path))
        chunk_size = 52428800
        chunk_count = int(math.ceil(source_size / float(chunk_size)))

        if verbose:
            print('chunk_count:', chunk_count)

        for i in range(chunk_count):
            if verbose:
                print('on chunk:', i)
            offset = chunk_size * i
            bytes = min(chunk_size, source_size - offset)
            with FileChunkIO(source_path, 'r', offset=offset, bytes=bytes) as fp:
                mp.upload_part_from_file(fp, part_num=i + 1)

        mp.complete_upload()

    def get_all_files(self):
        # get all files in bucket
        ret_files = []
        files = []
        for key in self.bucket.list():
            ret_files.append(key.name.encode('utf-8'))
            files.append(key)

        return ret_files, files

    def get_bucket_size(self):
        # returns total size of all things in bucket (up to 1000 things)
        size = 0
        for key in self.bucket.list():
            size += key.size

        return size

    def download_files(self, file_list, bucket_list, path_prefix='analytical360/images/'):
        for f, l in zip(file_list, bucket_list):
            path = path_prefix + f
            if not os.path.exists(path):
                print('downloading', f)
                l.get_contents_to_filename(path)
            else:
                print('already have', f)

if __name__ == "__main__":
    pics1 = list(glob.iglob('analytical360/archive_images/*.jpg'))
    pics2 = list(glob.iglob('analytical360/new_images/*.jpg'))
    aws = awsS3()
    # for testing
    # source_path = pics1[1]
    # aws.upload_big_file(source_path)

    # to download all files:
    # if not os.path.exists('analytical360/images/'):
    #     os.mkdir('analytical360/images/')
    # files, bucket_list = aws.get_all_files()
    # aws.download_files(files, bucket_list)

    # to upload all files from local:
    # files, bucket_list = aws.get_all_files()
    # files = set(files)
    # pics1fnames = [f.split('/')[-1] for f in pics1]
    # pics2fnames = [f.split('/')[-1] for f in pics2]
    # for i, p in enumerate(pics2): # also do for pics1
    #     if p not in files:
    #         print 'on file:', p
    #         aws.upload_big_file(p)
    #     else:
    #         print p, 'already there'
