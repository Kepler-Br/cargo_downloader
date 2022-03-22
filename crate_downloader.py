#!/bin/python3

import os.path
import sys
from typing import Union

import requests as requests
from tqdm import tqdm
import toml
import argparse


class RequestResult:
    def __init__(self, content: Union[bytearray, None], status_code: int):
        self._content = content
        self._response_code = status_code

    def get_content(self) -> bytearray:
        return self._content

    def get_status_code(self) -> int:
        return self._response_code


class CrateDownloadError(Exception):
    def __init__(self, link: str, code: int):
        self.link = link
        self.code = code


def get_link_with_progress(link: str, progress_text: str) -> RequestResult:
    response = requests.get(link, stream=True)
    total_length = response.headers.get('content-length')
    chunk_size = 4096

    if response.status_code != 200:
        return RequestResult(content=None, status_code=response.status_code)

    content = None
    status_code = 200

    if total_length is None:  # no content length header
        progress_bar = tqdm(
            desc=progress_text,
            iterable=response.iter_content(chunk_size=chunk_size),
            unit='KB',
            bar_format='{l_bar}{bar}{r_bar:3.0f}',
            unit_scale=1e-3,
            leave=False, )

        content = bytearray()

        for data in progress_bar:
            progress_bar.update(len(data))
            content += data
        progress_bar.close()
    else:
        total_length = int(total_length)
        progress_bar = tqdm(
            desc=progress_text,
            iterable=response.iter_content(chunk_size=chunk_size),
            total=float(total_length) + 1,
            unit='KB',
            bar_format='{desc}: {percentage:3.0f}%|{bar}| {n:.3f}/{total:.3f} [{elapsed}<{remaining}, '
                       '{rate_fmt}{postfix}]',
            unit_scale=1e-3,
            leave=False, )

        content = bytearray()

        for data in progress_bar:
            progress_bar.update(len(data))
            content += data
        progress_bar.close()

    return RequestResult(content=content, status_code=status_code)


def parse_arguments():
    arg_parser = argparse.ArgumentParser(description='Mirror cargo.io crates.')

    arg_parser.add_argument('cargo_lock_file', help='specify a path to a Cargo.lock',
                            action='store', type=str)

    arg_parser.add_argument('--overwrite', '-o', help='overwrite existing crates',
                            action='store_true', required=False)

    arg_parser.add_argument('--repo', '-r', help='crates repo link',
                            action='store', type=str, default='https://crates.io',
                            required=False, dest='repo_link')

    arg_parser.add_argument('--output', '-O', help='output directory',
                            action='store', type=str, default='./',
                            required=False, dest='output_dir')

    arg_parser.add_argument('--exit-on-error', '-e', help='exit program if download error encountered',
                            action='store_true', required=False)

    arg_parser.add_argument('--err-log', '-l', help='output error log to file. If not specified, stderr used instead',
                            action='store', default=None, required=False)

    return arg_parser.parse_args()


def download_crate(crate_io_link: str, local_path: str, name: str, version: str, overwrite_existing: bool):
    link = os.path.join(crate_io_link, 'api/v1/crates/', name, version, 'download')
    dir_path = os.path.join(local_path, 'api/v1/crates/', name, version)
    crate_path = os.path.join(dir_path, 'download')

    if not overwrite_existing and os.path.exists(crate_path):
        return

    result = get_link_with_progress(link, f'Downloading {name}:{version}')
    if result.get_status_code() != 200:
        raise CrateDownloadError(link, result.get_status_code())

    os.makedirs(dir_path, exist_ok=True)

    with open(crate_path, 'wb') as handle:
        handle.write(result.get_content())


def main():
    args = parse_arguments()

    try:
        with open(args.cargo_lock_file, 'r') as handle:
            cargo_lock = toml.loads(handle.read())
    except toml.TomlDecodeError as e:
        print(f'Error parsing {args.cargo_lock_file}:', file=sys.stderr)
        print(f'{e}', file=sys.stderr)
        return -1
    except FileNotFoundError as e:
        print(f'Error reading {args.cargo_lock_file}:', file=sys.stderr)
        print(f'{e}', file=sys.stderr)
        return -1

    if args.err_log is None:
        err_log_file = sys.stderr
    else:
        err_log_file = open(args.err_log, 'w')

    crates_progress_bar = tqdm(
        desc=f'Crates to download',
        iterable=cargo_lock['package'],
        leave=False, )

    for package in crates_progress_bar:
        package_name = package['name']
        package_version = package['version']
        try:
            download_crate(args.repo_link, args.output_dir, package_name, package_version, args.overwrite)
        except CrateDownloadError as e:
            print(
                f'Error downloading crate "{package_name}", version {package_version} with http code {e.code}. '
                f'Link: {e.link}',
                file=err_log_file)
            if args.exit_on_error:
                return -1

    if err_log_file != sys.stderr:
        err_log_file.close()

    return 0


if __name__ == '__main__':
    sys.exit(main())
