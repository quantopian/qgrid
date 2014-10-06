import pandas as pd
import numpy as np
import os
import uuid
import json

from IPython.display import display_html, display_javascript


def template_contents(filename):
    template_filepath = os.path.join(
        os.path.dirname(__file__),
        'templates',
        filename,
    )
    with open(template_filepath) as f:
        return f.read()


SLICK_GRID_CSS = template_contents('slickgrid.css.template')
SLICK_GRID_JS = template_contents('slickgrid.js.template')


class SlickGrid(object):

    def __init__(self, data_frame, remote_js=False):
        self.data_frame = data_frame
        self.remote_js = remote_js
        self.div_id = str(uuid.uuid4())

        self.df_copy = data_frame.copy()

        if type(self.df_copy.index) == pd.core.index.MultiIndex:
            self.df_copy.reset_index(inplace=True)
        else:
            self.df_copy.insert(0, self.df_copy.index.name, self.df_copy.index)

        tc = dict(np.typecodes)
        for key in np.typecodes.keys():
            if "All" in key:
                del tc[key]

        self.column_types = []
        for col_name, dtype in self.df_copy.dtypes.iteritems():
            column_type = {'field': col_name}
            for type_name, type_codes in tc.items():
                if dtype.kind in type_codes:
                    column_type['type'] = type_name
                    break
            self.column_types.append(column_type)

        self.precision = pd.get_option('display.precision') - 1

    def _ipython_display_(self):
        try:
            column_types_json = json.dumps(self.column_types)
            data_frame_json = self.df_copy.to_json(
                orient='records',
                date_format='iso',
                double_precision=self.precision,
            )

            if self.remote_js:
                cdn_base_url = \
                    "https://rawgit.com/quantopian/qgrid/master/qgrid/qgridjs"
            else:
                cdn_base_url = "/nbextensions/qgridjs"

            raw_html = SLICK_GRID_CSS.format(
                div_id=self.div_id,
                cdn_base_url=cdn_base_url,
            )
            raw_js = SLICK_GRID_JS.format(
                cdn_base_url=cdn_base_url,
                div_id=self.div_id,
                data_frame_json=data_frame_json,
                column_types_json=column_types_json,
            )

            display_html(raw_html, raw=True)
            display_javascript(raw_js, raw=True)
        except Exception as err:
            display_html('ERROR: {}'.format(str(err)), raw=True)
