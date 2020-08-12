"""
When exporting assignments from Moodle, we get one ZIP file (with strange Windows char encoding inside).
The structure is:
word_id_assignsubmission [folder]
     name_decided_by_user.zip
...


The required output is:
extracted/
   user id1_id2 if part of zip name or TBD /
      files in the internal zip

"""
import os
import shutil
import sys
import tempfile
import zipfile

used_names = set()


def validName(aName):
    """@:return True if aName complies to the regex and that it is the first time this name is checked"""
    if aName in used_names:
        return False
    used_names.add(aName)
    # can add here regex checking
    return True


if __name__ == "__main__":
    import argparse

    # parser = argparse.ArgumentParser()
    # parser.add_argument("file", help="input file name (ZIP)")
    # args = parser.parse_args()

    if len(sys.argv) != 2:
        sys.exit(0)
    path_to_zip_file =sys.argv[1]

    tmp_dir = tempfile.mkdtemp(dir='.')
    directory_to_extract_to = "extracted"

    with zipfile.ZipFile(path_to_zip_file, 'r') as zip_ref:
        zip_ref.extractall(tmp_dir)
    print("extraction 1 completed")
    for root, dirs, files in os.walk(tmp_dir, topdown=True):
        for f in files:
            dir_name = f.split('.')[0]
            if not validName(dir_name):
                print("directory %s is skipped. invalid name or duplicated" % dir_name)
                continue
            with zipfile.ZipFile(os.path.join(root,f), 'r') as z:
                z.extractall(os.path.join(directory_to_extract_to,dir_name))

    shutil.rmtree(tmp_dir)
    print("now run\n./moss.pl -l java -d ~/Downloads/94219/ex2/extracted/*/src/part2/*.java")