from src.dpi import enable_dpi_awareness


enable_dpi_awareness()

from src.app import CVInputApp


def main():
    app = CVInputApp()
    app.run()


if __name__ == "__main__":
    main()
