import random
import string

from dvc_fs.management.create_dvc_repo_github import \
    create_github_dvc_temporary_repo_with_s3


def test_basic_operations():
    with create_github_dvc_temporary_repo_with_s3(
        "covid-genomics", "temporary_dvc_repo"
    ) as fs:

        # List of files that will be created
        files_to_create = ["test1.txt", "dir/test2.txt", "dir/dir/test3.txt"]

        for path in files_to_create:
            text_file_contents = f"Hello world! {''.join(random.choices(string.ascii_lowercase + string.digits, k=20))}"

            # Check basic writing operation
            fs.writetext(path, text_file_contents)
            assert fs.readtext(path) == text_file_contents

        # All files must return exists(...) == True
        for path in files_to_create:
            assert fs.exists(path)

        # Check if exists(...) returns False for files that do not exist
        for path in [
            "test2.txt",
            "test.1.txt",
            "dir/dir/test1.txt",
            "dir/test1.txt",
        ]:
            assert not fs.exists(path)

        # Check if fs.walk returns correct files
        list_of_files = set(fs.walk.files())
        assert list_of_files == set([f"/{path}" for path in files_to_create])

        # Check for removing files
        for path in files_to_create:
            assert fs.exists(path)

            # Now remove file and check if exists() correctly returns False
            fs.remove(path)
            assert not fs.exists(path)
        
        # We removed all files so the walk should return 0
        list_of_files = set(fs.walk.files())
        assert len(list_of_files) == 0