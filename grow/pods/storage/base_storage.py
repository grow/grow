class BaseStorage(object):

    is_cloud_storage = False

    @staticmethod
    def read(filename):
        raise NotImplementedError

    @staticmethod
    def open(filename, mode='r'):
        raise NotImplementedError

    @staticmethod
    def modified(filename):
        raise NotImplementedError

    @staticmethod
    def size(filename):
        raise NotImplementedError

    @staticmethod
    def stat(filename):
        raise NotImplementedError

    @staticmethod
    def listdir(dirpath, recursive=True):
        raise NotImplementedError

    @staticmethod
    def walk(dirpath):
        raise NotImplementedError

    @staticmethod
    def delete(filename):
        raise NotImplementedError

    @staticmethod
    def delete_dir(dirpath):
        raise NotImplementedError

    @staticmethod
    def delete_files(dirpaths, recursive=False, pattern=None):
        raise NotImplementedError

    @staticmethod
    def JinjaLoader(path):
        raise NotImplementedError

    @staticmethod
    def copy_to(path, target_path):
        raise NotImplementedError

    @staticmethod
    def move_to(path, target_path):
        raise NotImplementedError

    @classmethod
    def write(cls, path, content):
        file_obj = cls.open(path, mode='w')
        file_obj.write(content)
        return file_obj

    @classmethod
    def update_headers(cls, headers, path):
        pass
