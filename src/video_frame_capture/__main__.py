"""应用入口 - 同时支持 GUI 和 CLI 模式"""

import sys
import os


def main():
    """主入口
    
    检测启动方式：
    - 如果有 --cli / --headless 参数 → CLI 模式
    - 如果是命令行管道调用 (piped) → CLI 模式
    - 否则 → GUI 模式
    """
    # CLI 模式检测
    cli_flags = {"--cli", "--headless", "--help", "--version", "info", "extract", "ls"}

    if len(sys.argv) > 1:
        first_arg = sys.argv[1]
        if first_arg in cli_flags or first_arg.startswith("-"):
            # 走 CLI
            from .cli.app import main as cli_main
            sys.exit(cli_main())

    # GUI 模式
    try:
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtCore import Qt
        from .gui.main_window import MainWindow
        from .gui.i18n import I18N
    except ImportError:
        # 没有 PyQt6，自动降级到 CLI
        print("⚠️  PyQt6 未安装，切换至 CLI 模式", file=sys.stderr)
        from .cli.app import main as cli_main
        sys.exit(cli_main())

    if hasattr(Qt, "AA_EnableHighDpiScaling"):
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
    if hasattr(Qt, "AA_UseHighDpiPixmaps"):
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setApplicationName("VideoFrameCapture")
    app.setApplicationVersion("0.1.1")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
