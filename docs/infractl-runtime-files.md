# Runtime files

The runtime optional parameter `files` allows specifying files and directories that must be present in runtime.

Runtime files can be used for:

* Copy local files and directories to the specified location in runtime, so a deployed program can use them.
* Copy files and directories from a remote location to the specified location in runtime (to be implemented).
* Extract local and remote archives to the specified location in runtime (to be implemented).

Example:

```python
runtime = infractl.runtime(
    # 'data.csv' from the local working directory will be copied to the runtime working directory 
    files=['data.csv'],
)
await infractl.run(infractl.program('my_flow.py'), runtime=runtime)
```

The value for `files` is a list, where each item is:

* `str`
* `dict`
* instance of `infractl.base.RuntimeFile`

A `str` item is converted to `infractl.base.RuntimeFile` with `src` equal to the item:

```python
runtime1 = infractl.runtime(files=['foo'])
runtime2 = infractl.runtime(files=[RuntimeFile(src='foo')])
```

A `dict` item is converted `infractl.base.RuntimeFile` with arguments from the dict:

```python
runtime1 = infractl.runtime(files=[{'src': 'foo', 'dst': 'bar'}])
runtime2 = infractl.runtime(files=[RuntimeFile(src='foo', dst='bar')])
```

Currently, runtime files are supported only for Prefect programs.

## Local files

* If `src` does not have a scheme (https://en.wikipedia.org/wiki/Uniform_Resource_Identifier#Syntax) then it is a local path.
* If `src` or `dst` ends with '/', then it is a directory, otherwise it is a file.
* Current local working directory is used for relative path in `src`.
* Current working directory in the runtime is used for relative path in `dst`.

```python
# Copy local file `file1` to the current directory in runtime.
'file1'  # or {'src': 'file1'}
```

```python
# Copy local file `data/file1` to `file1` in the current directory in runtime.
'data/file1'  # or {'src': 'data/file1'}
```

```python
# Copy local file `file1` to `file2` in the current directory in runtime.
{'src': 'file1', 'dst': 'file2'}
```

```python
# Copy local file `/data/file1` to `file2` in the current directory in runtime.
{'src': 'data/file1', 'dst': 'file2'}
```

```python
# Copy local file `/tmp/file1` to `file1` in the current directory in runtime.
'/tmp/file1'  # or {'src': '/tmp/file1'}
```

```python
# Copy local file `/tmp/file1` to `file2` in the current directory in runtime.
{'src': '/tmp/file1', 'dst': 'file2'}
```

```python
# TODO: Copy local file `'~/.docker/config.json` to `~/.docker/config.json` in the runtime.
# Note: destination directory `~/.docker/` will be created if does not exists, with all parent directories.
# Note: tilda ('~') in `src` and `dst`is converted to the correct local and runtime path (`HOME` can be different)
{'src': '~/.docker/config.json', 'dst': '~/.docker/'}
```

```python
# Copy a content of local directory `data/` recursively to the current directory in runtime.
'data/'  # or {'src': 'data/'} 
```

```python
# Copy a content of local directory `data/` recursively to 'data/' in the current directory in runtime.
{'src': 'data/', 'dst': 'data/'}
```

```python
# TODO: Copy all csv files from local 'data/' directory to the current directory in runtime.
'data/*.csv'  # or {'src': 'data/*.csv'} 
```

```python
# TODO: Copy all csv files from local 'data/' directory to 'data/' the current directory in runtime.
# Note: destination directory `data/` will be created if does not exists, with all parent directories.
{'src': 'data/*.csv', 'dst': 'data/'}
```

```python
# TODO: Copy all csv files from local 'data/' directory and subdirectories to the current directory in runtime.
# Subdirectories of 'data/' will be created 
'data/**/*.csv'  # or {'src': 'data/*.csv'} 
```

## Archives

```python
# TODO: Extract archive 'archive.zip` from the local current directory to the current directory in runtime.
'zip:data.zip'
```

Supported archive schemas: "zip", "tar", "tgz".

## Remote files

```python
# TODO: Copy remote file from the URL to the current directory in runtime.
'https://github.com/ray-project/test_dag/archive/41d09119cbdf8450599f993f51318e9e27c59098.zip'
```

```python
# TODO: Extract remote archive from the URL to the current directory in runtime.
'zip+https://github.com/ray-project/test_dag/archive/41d09119cbdf8450599f993f51318e9e27c59098.zip'
```

Supported remote schemas: "http", "https", "s3".

## Ignore files (TODO)

* Ignore file to skip for bulk operations (directories or archives).
  * .dockerignore (https://docs.docker.com/engine/reference/builder/#dockerignore-file)
  * .gitignore
  * ignore list (without physical ignore file on disk)

## Other (possible?) parameters (TODO)

* Enable/disable recursive copy/extraction.
* Ignore missing files: do not raise an exception if there are no matching files for `src`.
* Flatten files: when copying recursively or extracting do not create subdirectories in `dst`.
* User script: user-provided Bash script to set up runtime.
