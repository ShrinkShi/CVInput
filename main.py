from src.dpi import enable_dpi_awareness, set_app_user_model_id


enable_dpi_awareness()
set_app_user_model_id()

from src.app import CVInputApp


def main():
    app = CVInputApp()
    app.run()


if __name__ == "__main__":
    main()
