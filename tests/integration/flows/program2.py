import os.path

if __name__ == '__main__':
    missing_files = []

    def assert_file_exists(name: str):
        """Checks if the files exists"""

        if os.path.isfile(name):
            print(f'File {name} exists')
        else:
            print(f'File {name} does not exist')
            missing_files.append(name)

    assert_file_exists('test_file.txt')
    assert_file_exists('test_file.txt.renamed')
    assert_file_exists('new_data/test_file.txt')

    if missing_files:
        raise AssertionError(f'Missing files: {missing_files}')
