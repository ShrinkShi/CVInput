def widget_exists(widget):
    try:
        return widget is not None and bool(widget.winfo_exists())
    except Exception:
        return False
