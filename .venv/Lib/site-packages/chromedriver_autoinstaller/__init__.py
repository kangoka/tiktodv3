# coding: utf-8

import logging
import os
from typing import AnyStr, Optional

from . import utils


def install(cwd: bool = False, path: Optional[AnyStr] = None, no_ssl: bool = False):
    """
    Appends the directory of the chromedriver binary file to PATH.

    :param cwd: Flag indicating whether to download to current working directory. If the `cwd` is True, then path argument will be ignored.
    :param path: Specify the path where the Chrome driver will be installed. If the `cwd` value is True, this value is ignored.
    :param no_ssl: Determines whether or not to use the encryption protocol when downloading the chrome driver.
    :return: The file path of chromedriver
    """
    if cwd:
        path = os.getcwd()
    chromedriver_filepath = utils.download_chromedriver(path, no_ssl)
    if not chromedriver_filepath:
        logging.debug("Can not download chromedriver.")
        return
    chromedriver_dir = os.path.dirname(chromedriver_filepath)
    if "PATH" not in os.environ:
        os.environ["PATH"] = chromedriver_dir
    elif chromedriver_dir not in os.environ["PATH"]:
        os.environ["PATH"] = (
            chromedriver_dir + utils.get_variable_separator() + os.environ["PATH"]
        )
    return chromedriver_filepath


def get_chrome_version():
    """
    Get installed version of chrome on client

    :return: The version of chrome
    """
    return utils.get_chrome_version()
