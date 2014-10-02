import pandas as pd
import numpy as np
from textwrap import dedent
import uuid
import json

from IPython.display import display_html, display_javascript

SLICK_GRID_CSS = dedent(
    """
    <script type="text/javascript">
    if ($("#dg-css").length == 0){{
        $("head").append([
            "<link href='{cdn_base_url}/lib/slick.grid.css' rel='stylesheet'>",
            "<link href='{cdn_base_url}/lib/slick-default-theme.css' rel='stylesheet'>",
            "<link href='http://cdnjs.cloudflare.com/ajax/libs/jqueryui/1.10.4/css/jquery-ui.min.css' rel='stylesheet'>",
            "<link id='dg-css' href='{cdn_base_url}/datagrid.css' rel='stylesheet'>"
        ]);
    }}
    </script>
    <div class='q-grid-container'>
    <div id='{div_id}' class='q-grid'></div>
    </div>
    """
)

SLICK_GRID_JS = dedent(
    """
    var self = this;
    require.config({{
        paths: {{
            jquery_drag: "{cdn_base_url}/lib/jquery.event.drag-2.2",
            slick_core: "{cdn_base_url}/lib/slick.core.2.2",
            slick_data_view: "{cdn_base_url}/lib/slick.dataview.2.2",
            slick_grid: "{cdn_base_url}/lib/slick.grid.2.2",
            data_grid: "{cdn_base_url}/datagrid",
            date_filter: "{cdn_base_url}/datagrid.datefilter",
            slider_filter: "{cdn_base_url}/datagrid.sliderfilter",
            filter_base:  "{cdn_base_url}/datagrid.filterbase",
            handlebars: "{cdn_base_url}/lib/handlebars-v2.0.0",
            jquery: [
                "components/jquery/jquery.min",
                "/static/js/jquery.min"
            ],
            underscore: [
                "components/underscore/underscore-min",
                "http://cdnjs.cloudflare.com/ajax/libs/underscore.js/1.7.0/underscore-min"
            ],
            moment: [
                "components/moment/moment",
                "http://cdnjs.cloudflare.com/ajax/libs/moment.js/2.8.3/moment.min"
            ],
            jqueryui: [
                "components/jquery-ui/ui/minified/jquery-ui.min",
                "http://cdnjs.cloudflare.com/ajax/libs/jqueryui/1.10.4/jquery-ui.min"
            ]
        }}
    }});

    require([
        'jquery',
        'jquery_drag',
        'slick_core',
        'slick_data_view'
    ],
    function($){{
        $('#{div_id}').closest('.rendered_html').removeClass('rendered_html');
        require(['slick_grid'], function(){{
            require(["data_grid"], function(dgrid){{
                var grid = new dgrid.DataGrid('#{div_id}', {data_frame_json}, {column_types_json});
                grid.initialize_slick_grid();
            }});
        }});
    }});
    """
)

class QuantopianGrid(object):
    def __init__(self, data_frame):
        self.data_frame = data_frame
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
            found_type = False
            column_type = {'field': col_name}
            for type_name, type_codes in tc.items():
                if dtype.kind in type_codes:
                    found_type = True
                    column_type['type'] = type_name
                    break
            self.column_types.append(column_type)

        self.precision = pd.get_option('display.precision') - 1

    def _ipython_display_(self):
        try:
            column_types_json = json.dumps(self.column_types)
            data_frame_json = self.df_copy.to_json(orient="records", double_precision=self.precision)

            debug = True
            if debug:
                cdn_base_url = "/nbextensions"
            else:
                cdn_base_url = "https://rawgit.com/quantopian/SlickDataFrame/master"

            raw_html = SLICK_GRID_CSS.format(div_id=self.div_id, cdn_base_url=cdn_base_url)
            raw_js = SLICK_GRID_JS.format(cdn_base_url=cdn_base_url,
                                            div_id=self.div_id,
                                            data_frame_json=data_frame_json,
                                            column_types_json=column_types_json)

            display_html(raw_html, raw=True)
            display_javascript(raw_js, raw=True)
        except Exception, err:
            display_html('ERROR: %s\n' % str(err))

def qgrid(dataframe):
    return QuantopianGrid(dataframe)

def load_ipython_extension(ipython):
    """
    Entrypoint for ipython.  Add objects to the user's namespace by adding them
    to the dictionary passed to ipython.push.
    """
    ipython.push(
        {
            'qgrid': qgrid
        }
    )
