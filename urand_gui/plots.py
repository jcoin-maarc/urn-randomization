from bokeh.embed import components
from bokeh.models import (
    ColumnDataSource,
    Paragraph,
    Legend,
    CDSView,
    GroupFilter,
    IndexFilter,
    Select,
    HoverTool,
    FactorRange,
    PrintfTickFormatter,
)
from bokeh.plotting import figure
from bokeh.layouts import column, row
from bokeh.resources import INLINE
from bokeh.transform import factor_cmap
from bokeh.core.properties import value
from bokeh.palettes import Dark2_5 as bokeh_palette
from bokeh.models.callbacks import CustomJS
import itertools

palette = ["#ba32a0", "#f85479", "#f8c260", "#00c2ba"]

chart_font = "Helvetica"
chart_title_font_size = "16pt"
chart_title_alignment = "center"
axis_label_size = "14pt"
axis_ticks_size = "12pt"
default_padding = 30
chart_inner_left_padding = 0.015
chart_font_style_title = "bold italic"


def palette_generator(length, palette):
    int_div = length // len(palette)
    remainder = length % len(palette)
    return (palette * int_div) + palette[:remainder]


def plot_styler(p):
    p.title.text_font_size = chart_title_font_size
    p.title.text_font = chart_font
    p.title.align = chart_title_alignment
    p.title.text_font_style = chart_font_style_title
    p.y_range.start = 0
    p.x_range.range_padding = chart_inner_left_padding
    p.xaxis.axis_label_text_font = chart_font
    p.xaxis.major_label_text_font = chart_font
    p.xaxis.axis_label_standoff = int(default_padding * 0.3)
    p.xaxis.axis_label_text_font_size = axis_label_size
    p.xaxis.major_label_text_font_size = axis_ticks_size
    p.yaxis.axis_label_text_font = chart_font
    p.yaxis.major_label_text_font = chart_font
    p.yaxis.axis_label_text_font_size = axis_label_size
    p.yaxis.major_label_text_font_size = axis_ticks_size
    p.yaxis.axis_label_standoff = int(default_padding * 0.3)
    p.toolbar.logo = None
    p.toolbar_location = None
    p.x_range.range_padding = 0.1
    p.legend.background_fill_alpha = 0.0
    p.xaxis.major_label_orientation = 0.18
    p.xgrid.grid_line_color = None
    p.legend.location = "top_right"
    # p.legend.orientation = "vertical"
    p.sizing_mode = "scale_both"
    p.xaxis.axis_label_text_font_size = "7pt"
    p.xaxis.major_label_text_font_size = "7pt"
    p.yaxis.axis_label_text_font_size = "7pt"
    p.yaxis.major_label_text_font_size = "7pt"


def plt_factor_treatment_assignments(study):
    factors = list(study.factors.keys())
    title_select_factor = Paragraph(
        text="Factor:", sizing_mode="stretch_both", align="end"
    )
    select_factor = Select(
        title="",
        value=factors[0],
        options=factors,
        sizing_mode="stretch_both",
        align="start",
        width_policy="fit",
    )

    pdf_urns = study.get_study_urns()
    pdf_all = study.export_history()
    pdf_all = (
        pdf_all.groupby("trt")
        .size()
        .reset_index()
        .rename(columns={0: "n_participants"})
    )
    n_participants = pdf_all["n_participants"].sum()
    tooltips_all = [("No. participants", "@n_participants")]
    p_all = figure(
        x_range=study.treatments,
        plot_height=200,
        plot_width=300,
        title="All participants ({0})".format(n_participants),
        toolbar_location=None,
        tools="",
        tooltips=tooltips_all,
        sizing_mode="stretch_both",
        height_policy="fit",
    )
    source_all = ColumnDataSource(data=pdf_all[["trt", "n_participants"]])
    p_all.add_tools(HoverTool(tooltips=[("No. participants", "@n_participants")]))
    p_all.vbar(x="trt", top="n_participants", width=0.9, alpha=0.9, source=source_all)
    p_all.xgrid.grid_line_color = None
    p_all.y_range.start = 0

    p_all.yaxis.axis_label = "No. participants"
    p_all.xaxis.axis_label = "Treatment"
    plot_styler(p_all)

    pdf_factors = pdf_urns.assign(
        **dict(
            [
                (
                    "pc_trt_{0}".format(trt).replace("-", ""),
                    pdf_urns["trt_{0}".format(trt)]
                    * 100
                    / pdf_urns[
                        [col for col in pdf_urns.columns if col.startswith("trt_")]
                    ].sum(axis=1),
                )
                for trt in study.treatments
            ]
        )
    )
    pdf_factors = pdf_factors.assign(
        **dict(
            [
                (trt, pdf_factors["pc_trt_{0}".format(trt).replace("-", "")])
                for trt in study.treatments
            ]
        )
    )
    tooltips = [
        ("Trtmt {0} ".format(trt), "@pc_trt_{0}".format(trt.replace("-", "")))
        for trt in study.treatments
    ]
    src = ColumnDataSource(data=pdf_factors)
    filter = GroupFilter(column_name="factor", group=factors[0])
    view = CDSView(source=src, filters=[filter])

    p = figure(
        plot_height=200,
        plot_width=300,
        title="By factor",
        toolbar_location=None,
        tools="",
        tooltips=tooltips,
        x_range=FactorRange(),
        y_range=[0, 110],
        sizing_mode="stretch_both",
        height_policy="fit",
    )
    p.x_range.factors = study.factors[factors[0]]
    lst_color = list(
        itertools.islice(itertools.cycle(bokeh_palette), len(study.treatments))
    )
    lst_vbar = p.vbar_stack(
        [trt for trt in study.treatments],
        x="factor_level",
        width=0.9,
        alpha=0.5,
        color=lst_color,
        source=src,
        view=view,
    )
    legend = Legend(
        items=[
            (trt, [plt_vbar]) for (trt, plt_vbar) in zip(study.treatments, lst_vbar)
        ],
        location=(0, 30),
        title="Treatments",
    )
    p.add_layout(legend, "right")
    p.yaxis.axis_label = "Percentage"
    p.xaxis.axis_label = "Factor levels"
    plot_styler(p)

    callback = CustomJS(
        args=dict(
            select=select_factor, src=src, filter=filter, factors=study.factors, plot=p
        ),
        code="""
		  filter.group = select.value
		  filter.change.emit()
		  src.change.emit()
		  plot.x_range.factors = factors[select.value]
		""",
    )

    select_factor.js_on_change("value", callback)

    # select_factor.on_change('value', pick_new_factor)
    # grab the static resources
    js_resources = INLINE.render_js()
    css_resources = INLINE.render_css()
    script_p, div_p = components(
        row(
            p_all,
            column(
                row(title_select_factor, select_factor, align="end"),
                row(p, sizing_mode="stretch_both", height_policy="fit"),
            ),
            sizing_mode="stretch_both",
            height_policy="fit",
        )
    )
    return script_p, div_p, js_resources, css_resources
