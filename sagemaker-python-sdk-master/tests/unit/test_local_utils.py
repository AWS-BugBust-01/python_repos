# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"). You
# may not use this file except in compliance with the License. A copy of
# the License is located at
#
#     http://aws.amazon.com/apache2.0/
#
# or in the "license" file accompanying this file. This file is
# distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF
# ANY KIND, either express or implied. See the License for the specific
# language governing permissions and limitations under the License.
from __future__ import absolute_import

import pytest
from mock import patch, Mock

import sagemaker.local.utils


@patch("shutil.rmtree", Mock())
@patch("sagemaker.local.utils.recursive_copy")
def test_move_to_destination_local(recursive_copy):
    # local files will just be recursively copied
    sagemaker.local.utils.move_to_destination("/tmp/data", "file:///target/dir/", "job", None)
    recursive_copy.assert_called_with("/tmp/data", "/target/dir/")


@patch("shutil.rmtree", Mock())
@patch("sagemaker.local.utils.recursive_copy")
def test_move_to_destination_s3(recursive_copy):
    sms = Mock()

    # without trailing slash in prefix
    sagemaker.local.utils.move_to_destination("/tmp/data", "s3://bucket/path", "job", sms)
    sms.upload_data.assert_called_with("/tmp/data", "bucket", "path/job")
    recursive_copy.assert_not_called()

    # with trailing slash in prefix
    sagemaker.local.utils.move_to_destination("/tmp/data", "s3://bucket/path/", "job", sms)
    sms.upload_data.assert_called_with("/tmp/data", "bucket", "path/job")

    # without path, with trailing slash
    sagemaker.local.utils.move_to_destination("/tmp/data", "s3://bucket/", "job", sms)
    sms.upload_data.assert_called_with("/tmp/data", "bucket", "job")

    # without path, without trailing slash
    sagemaker.local.utils.move_to_destination("/tmp/data", "s3://bucket", "job", sms)
    sms.upload_data.assert_called_with("/tmp/data", "bucket", "job")


def test_move_to_destination_illegal_destination():
    with pytest.raises(ValueError):
        sagemaker.local.utils.move_to_destination("/tmp/data", "ftp://ftp/in/2018", "job", None)
