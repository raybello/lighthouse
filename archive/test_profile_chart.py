import dearpygui.dearpygui as dpg
import dearpygui.demo as demo

dpg.create_context()


dpg.add_texture_registry(label="Demo Texture Container", tag="__demo_texture_container")


def create_static_textures():
    ## create static textures
    border_width = 3  # Width of the dark border

    texture_data1 = []
    for i in range(100 * 100):
        texture_data1.append(255 / 255)
        texture_data1.append(0)
        texture_data1.append(255 / 255)
        texture_data1.append(255 / 255)

    texture_data2 = []
    for i in range(50 * 50):
        texture_data2.append(255 / 255)
        texture_data2.append(255 / 255)
        texture_data2.append(0)
        texture_data2.append(255 / 255)

    texture_data3 = []
    for row in range(100):
        for column in range(100):
            # Check if we're in the border region
            if (
                row < border_width
                or row >= 100 - border_width
                or column < border_width
                or column >= 100 - border_width
            ):
                # Dark border (dark green/black)
                texture_data3.append(0.1)  # R
                texture_data3.append(0.2)  # G
                texture_data3.append(0.1)  # B
                texture_data3.append(1.0)  # A
            else:
                # Forest green background
                texture_data3.append(34 / 255)  # R
                texture_data3.append(139 / 255)  # G
                texture_data3.append(34 / 255)  # B
                texture_data3.append(1.0)  # A

    # Add green texture
    texture_data4 = []
    for i in range(100 * 100):
        texture_data4.append(0)
        texture_data4.append(255 / 255)
        texture_data4.append(0)
        texture_data4.append(255 / 255)

    # Add cyan texture
    texture_data5 = []
    for i in range(100 * 100):
        texture_data5.append(0)
        texture_data5.append(255 / 255)
        texture_data5.append(255 / 255)
        texture_data5.append(255 / 255)

    dpg.add_static_texture(
        100,
        100,
        texture_data1,
        parent="__demo_texture_container",
        tag="__demo_static_texture_1",
        label="Static Texture 1",
    )
    dpg.add_static_texture(
        50,
        50,
        texture_data2,
        parent="__demo_texture_container",
        tag="__demo_static_texture_2",
        label="Static Texture 2",
    )
    dpg.add_static_texture(
        100,
        100,
        texture_data3,
        parent="__demo_texture_container",
        tag="__demo_static_texture_3",
        label="Static Texture 3",
    )
    dpg.add_static_texture(
        100,
        100,
        texture_data4,
        parent="__demo_texture_container",
        tag="__demo_static_texture_4",
        label="Static Texture 4",
    )
    dpg.add_static_texture(
        100,
        100,
        texture_data5,
        parent="__demo_texture_container",
        tag="__demo_static_texture_5",
        label="Static Texture 5",
    )


create_static_textures()

# Define image bounds for hover detection - expanded with more trace data
image_bounds = [
    # Read operations
    {
        "min": [0, -0.5],
        "max": [1, 0.5],
        "label": "Read Operation",
        "duration": "1.0ms",
        "time": "0ms - 1.0ms",
    },
    {
        "min": [4.2, -0.5],
        "max": [5.5, 0.5],
        "label": "Read Operation",
        "duration": "1.3ms",
        "time": "4.2ms - 5.5ms",
    },
    {
        "min": [7, -0.5],
        "max": [8.2, 0.5],
        "label": "Read Operation",
        "duration": "1.2ms",
        "time": "7.0ms - 8.2ms",
    },
    # Write operations
    {
        "min": [1.22, 0.5],
        "max": [3, 1.5],
        "label": "Write Operation",
        "duration": "1.78ms",
        "time": "1.22ms - 3.0ms",
    },
    {
        "min": [5.7, 0.5],
        "max": [6.8, 1.5],
        "label": "Write Operation",
        "duration": "1.1ms",
        "time": "5.7ms - 6.8ms",
    },
    {
        "min": [8.5, 0.5],
        "max": [10.2, 1.5],
        "label": "Write Operation",
        "duration": "1.7ms",
        "time": "8.5ms - 10.2ms",
    },
    # Network operations
    {
        "min": [2.5, 1.5],
        "max": [4, 2.5],
        "label": "Network Operation",
        "duration": "1.5ms",
        "time": "2.5ms - 4.0ms",
    },
    {
        "min": [6, 1.5],
        "max": [9, 2.5],
        "label": "Network Operation",
        "duration": "3.0ms",
        "time": "6.0ms - 9.0ms",
    },
    {
        "min": [9.5, 1.5],
        "max": [15, 2.5],
        "label": "Network Operation",
        "duration": "5.5ms",
        "time": "9.5ms - 15.0ms",
    },
]


def is_mouse_over_image(mouse_plot_pos, bounds):
    x, y = mouse_plot_pos
    return (
        bounds["min"][0] <= x <= bounds["max"][0]
        and bounds["min"][1] <= y <= bounds["max"][1]
    )


with dpg.window(label="Tutorial", width=900, height=500, tag="main_window"):

    with dpg.plot(label="Execution Profiling\n(double-click to reset)", height=400, width=-1, tag="main_plot"):
        dpg.add_plot_legend(outside=True,location=dpg.mvPlot_Location_NorthEast)

        process = (("Read", 0), ("Write", 1), ("Network", 2))

        with dpg.plot_axis(dpg.mvYAxis) as yaxis:
            dpg.set_axis_ticks(yaxis, process)
            dpg.fit_axis_data(yaxis)
            dpg.fit_axis_data(dpg.top_container_stack())

            # Read operations (yellow texture)
            dpg.add_image_series(
                "__demo_static_texture_2", [0, -0.5], [1, 0.5], label="read 1"
            )
            dpg.add_image_series(
                "__demo_static_texture_2", [4.2, -0.5], [5.5, 0.5], label="read 2"
            )
            dpg.add_image_series(
                "__demo_static_texture_2", [7, -0.5], [8.2, 0.5], label="read 3"
            )

            # Write operations (magenta/green textures)
            dpg.add_image_series(
                "__demo_static_texture_1", [1.22, 0.5], [3, 1.5], label="write 1"
            )
            dpg.add_image_series(
                "__demo_static_texture_4", [5.7, 0.5], [6.8, 1.5], label="write 2"
            )
            dpg.add_image_series(
                "__demo_static_texture_1", [8.5, 0.5], [10.2, 1.5], label="write 3"
            )

            # Network operations (mixed textures)
            dpg.add_image_series(
                "__demo_static_texture_1", [2.5, 1.5], [4, 2.5], label="network 1"
            )
            dpg.add_image_series(
                "__demo_static_texture_5", [6, 1.5], [9, 2.5], label="network 2"
            )
            dpg.add_image_series(
                "__demo_static_texture_3", [9.5, 1.5], [15, 2.5], label="network 3"
            )

        with dpg.plot_axis(dpg.mvXAxis, label="time(ms)") as xaxis:
            dpg.fit_axis_data(xaxis)
            dpg.fit_axis_data(dpg.top_container_stack())

        # Duration labels on traces
        dpg.draw_text((0.3, 0), "1.0ms", color=(0, 0, 0, 255), size=0.1)
        dpg.draw_text((2, 1), "1.78ms", color=(250, 250, 250, 255), size=0.1)
        dpg.draw_text((3, 2), "1.5ms", color=(250, 250, 250, 255), size=0.1)
        dpg.draw_text((4.7, 0), "1.3ms", color=(0, 0, 0, 255), size=0.1)
        dpg.draw_text((7.2, 2), "3.0ms", color=(0, 0, 0, 255), size=0.1)

    # Tooltip window (initially hidden)
    with dpg.window(
        label="Tooltip",
        tag="tooltip_window",
        show=False,
        no_title_bar=True,
        no_move=True,
        no_resize=True,
        no_collapse=True,
        autosize=True,
    ):
        dpg.add_text("", tag="tooltip_text1")
        dpg.add_text("", tag="tooltip_text2")
        dpg.add_text("", tag="tooltip_text3")


# Render loop to check mouse position
def update_tooltip(sender, app_data):

    # Get mouse position in plot coordinates
    mouse_plot_pos = dpg.get_plot_mouse_pos()
    # print(mouse_plot_pos)

    # Check if mouse is over any image
    tooltip_shown = False
    for bounds in image_bounds:
        if is_mouse_over_image(mouse_plot_pos, bounds):
            # Update tooltip content
            dpg.set_value("tooltip_text1", bounds["label"])
            dpg.set_value("tooltip_text2", f"Duration: {bounds['duration']}")
            dpg.set_value("tooltip_text3", f"Time: {bounds['time']}")

            # Position tooltip near mouse
            mouse_pos = dpg.get_mouse_pos(local=False)
            dpg.set_item_pos("tooltip_window", [mouse_pos[0] + 15, mouse_pos[1] + 15])
            dpg.configure_item("tooltip_window", show=True)
            tooltip_shown = True
            break

    if not tooltip_shown:
        dpg.configure_item("tooltip_window", show=False)


with dpg.handler_registry():
    dpg.add_mouse_move_handler(callback=update_tooltip)

dpg.create_viewport(title="Custom Title", width=1000, height=600)
dpg.setup_dearpygui()
dpg.show_viewport()
# demo.show_demo()
dpg.start_dearpygui()
dpg.destroy_context()
