import re

from ..debug_logger import debug_log


_GEOMETRY_RE = re.compile(r"^(?P<width>\d+)x(?P<height>\d+)(?P<x>[+-]\d+)(?P<y>[+-]\d+)$")


def widget_exists(widget):
    try:
        return widget is not None and bool(widget.winfo_exists())
    except Exception:
        return False


def coerce_window_size(value, fallback):
    try:
        value = int(value)
    except (TypeError, ValueError):
        value = 0
    if value > 1:
        return value
    try:
        fallback = int(fallback)
    except (TypeError, ValueError):
        fallback = 0
    return max(fallback, 1)


def parse_tk_geometry(geometry):
    match = _GEOMETRY_RE.match(str(geometry))
    if not match:
        return None
    return (
        int(match.group("x")),
        int(match.group("y")),
        int(match.group("width")),
        int(match.group("height")),
    )


def geometry_size_matches(window, width, height):
    try:
        window.update_idletasks()
        parsed = parse_tk_geometry(window.geometry())
        expected = (int(width), int(height))
        if parsed is not None:
            return (parsed[2], parsed[3]) == expected
        return (int(window.winfo_width()), int(window.winfo_height())) == expected
    except Exception:
        return False


def tk_geometry_rect(window, default_width=1, default_height=1):
    try:
        window.update_idletasks()
        geometry = window.geometry()
        match = _GEOMETRY_RE.match(geometry)
        if match:
            return (
                int(match.group("x")),
                int(match.group("y")),
                coerce_window_size(match.group("width"), default_width),
                coerce_window_size(match.group("height"), default_height),
            )
    except Exception:
        pass

    return (
        int(window.winfo_x()),
        int(window.winfo_y()),
        coerce_window_size(window.winfo_width(), default_width),
        coerce_window_size(window.winfo_height(), default_height),
    )


def window_visual_scale(window, logical_width, logical_height):
    visual_width = coerce_window_size(window.winfo_width(), logical_width)
    visual_height = coerce_window_size(window.winfo_height(), logical_height)
    scale_x = visual_width / logical_width if logical_width > 0 else 1
    scale_y = visual_height / logical_height if logical_height > 0 else 1
    if scale_x <= 0:
        scale_x = 1
    if scale_y <= 0:
        scale_y = 1
    return scale_x, scale_y, visual_width, visual_height


def left_attached_geometry(parent, child_width, child_height, gap=10):
    rect = tk_geometry_rect(
        parent,
        getattr(parent, "WIDTH", 1),
        getattr(parent, "HEIGHT", 1),
    )
    main_x, main_y, main_w, _main_h = rect
    scale_x, scale_y, main_visual_w, main_visual_h = window_visual_scale(parent, main_w, _main_h)
    child_visual_w = max(child_width, round(child_width * scale_x))
    child_visual_h = max(child_height, round(child_height * scale_y))

    screen_w = parent.winfo_screenwidth()
    screen_h = parent.winfo_screenheight()

    child_x = main_x - child_visual_w - gap
    child_y = main_y
    if child_x < 0:
        child_x = main_x + main_visual_w + gap

    child_x = max(0, min(child_x, max(0, screen_w - child_visual_w)))
    child_y = max(0, min(child_y, max(0, screen_h - child_visual_h)))
    debug_log(
        "WINDOW_POSITION",
        "left_attached_geometry",
        parent_geometry=parent.geometry(),
        tk_geometry_rect=rect,
        parent_winfo_x=parent.winfo_x(),
        parent_winfo_y=parent.winfo_y(),
        parent_winfo_rootx=parent.winfo_rootx(),
        parent_winfo_rooty=parent.winfo_rooty(),
        child_width=child_width,
        child_height=child_height,
        main_visual_w=main_visual_w,
        main_visual_h=main_visual_h,
        scale_x=round(scale_x, 4),
        scale_y=round(scale_y, 4),
        child_visual_w=child_visual_w,
        child_visual_h=child_visual_h,
        screen_w=screen_w,
        screen_h=screen_h,
        child_x=child_x,
        child_y=child_y,
    )
    return int(child_x), int(child_y)


def developer_panel_geometry(main, settings, child_width, child_height, settings_width, gap=10):
    main_rect = tk_geometry_rect(main, getattr(main, "WIDTH", 1), getattr(main, "HEIGHT", 1))
    main_x, main_y, main_w, main_h = main_rect
    scale_x, scale_y, main_visual_w, _main_visual_h = window_visual_scale(main, main_w, main_h)
    settings_visual_w = max(settings_width, round(settings_width * scale_x))
    child_visual_w = max(child_width, round(child_width * scale_x))
    child_visual_h = max(child_height, round(child_height * scale_y))
    screen_w = main.winfo_screenwidth()
    screen_h = main.winfo_screenheight()

    settings_left_x = main_x - settings_visual_w - gap
    if settings_left_x >= 0:
        left_of_settings_x = settings_left_x - child_visual_w - gap
        if left_of_settings_x >= 0:
            child_x = left_of_settings_x
            placement = "left_of_settings"
        else:
            child_x = main_x + main_visual_w + gap
            placement = "right_of_main"
    else:
        settings_rect = tk_geometry_rect(settings, settings_width, 1)
        settings_x = settings_rect[0]
        child_x = settings_x + settings_visual_w + gap
        placement = "right_of_settings"
        if child_x + child_visual_w > screen_w:
            left_of_main_x = main_x - child_visual_w - gap
            if left_of_main_x >= 0:
                child_x = left_of_main_x
                placement = "left_of_main_fallback"

    child_x = max(0, min(child_x, max(0, screen_w - child_visual_w)))
    child_y = max(0, min(main_y, max(0, screen_h - child_visual_h)))
    debug_log(
        "WINDOW_POSITION",
        "developer_panel_geometry",
        main_geometry=main.geometry(),
        settings_geometry=settings.geometry(),
        placement=placement,
        child_width=child_width,
        child_height=child_height,
        child_x=child_x,
        child_y=child_y,
    )
    return int(child_x), int(child_y)
