# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
import gzip

from email import encoders
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart


class Multipart(object):
    MIME = {
        '#include': 'text/x-include-url',
        '#include-once': 'text/x-include-once-url',
        '#!': 'text/x-shellscript',
        '#cloud-config': 'text/cloud-config',
        '#cloud-config-archive': 'text/cloud-config-archive',
        '#upstart-job': 'text/upstart-job',
        '#part-handler': 'text/part-handler',
        '#cloud-boothook': 'text/cloud-boothook'
    }

    def __init__(self):
        self.container = MIMEMultipart()

    def add(self, path, custom_mime_type="text/plain"):
        main_type, sub_type = self.determine_mime_type(path, custom_mime_type)
        if main_type == 'text':
            msg = self._add_text(path, sub_type)
        else:
            msg = self._add_base(path, main_type, sub_type)
        msg.add_header('Content-Disposition', 'attachment', filename=os.path.basename(path))
        self.container.attach(msg)

    def _add_text(self, path, sub_type):
        with open(path) as fo:
            return MIMEText(fo.read(), _subtype=sub_type)

    def _add_base(self, path, main_type, sub_type):
        with open(path, 'rb') as fo:
            msg = MIMEBase(main_type, sub_type)
            msg.set_payload(fo.read())
            encoders.encode_base64(msg)
            return msg

    def determine_mime_type(self, path, default="text/plain"):
        with open(path, 'rb') as fo:
            line = fo.readline()
        mime_type = default
        for shebang in Multipart.MIME.keys():
            if line.startswith(shebang):
                mime_type = Multipart.MIME[shebang]
                break
        return mime_type.split('/', 1)

    def save(self, path, compress=False):
        with open(path, 'wb') as fo:
            if compress:
                with gzip.GzipFile(fileobj=fo, filename=path) as gz:
                    gz.write(self.container.as_string())
            else:
                fo.write(self.container.as_string())

    def __str__(self):
        return self.container.as_string()
