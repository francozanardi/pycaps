import subprocess
import sys
from pathlib import Path
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                              QHBoxLayout, QLabel, QLineEdit, QPushButton,
                              QComboBox, QFileDialog, QMessageBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

class PycapsGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pycaps Transcribe")
        self.setGeometry(100, 100, 600, 350)

        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)

        # Title
        title = QLabel("Pycaps Video Transcriber")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # File selection
        file_layout = QHBoxLayout()
        file_label = QLabel("Video File:")
        file_label.setMinimumWidth(120)
        self.file_input = QLineEdit()
        self.file_input.setPlaceholderText("Select a video file...")
        browse_btn = QPushButton("Browse")
        browse_btn.clicked.connect(self.browse_file)
        file_layout.addWidget(file_label)
        file_layout.addWidget(self.file_input)
        file_layout.addWidget(browse_btn)
        layout.addLayout(file_layout)

        # Model selection
        model_layout = QHBoxLayout()
        model_label = QLabel("Whisper Model:")
        model_label.setMinimumWidth(120)
        self.model_combo = QComboBox()
        self.model_combo.addItems(["tiny", "base", "small", "medium", "large-v3"])
        self.model_combo.setCurrentText("large-v3")
        model_layout.addWidget(model_label)
        model_layout.addWidget(self.model_combo)
        layout.addLayout(model_layout)

        # Language selection
        lang_layout = QHBoxLayout()
        lang_label = QLabel("Language:")
        lang_label.setMinimumWidth(120)
        self.lang_combo = QComboBox()
        self.lang_combo.addItems(["italian", "english", "spanish", "french", "german", "portuguese", "chinese", "japanese"])
        self.lang_combo.setCurrentText("italian")
        lang_layout.addWidget(lang_label)
        lang_layout.addWidget(self.lang_combo)
        layout.addLayout(lang_layout)

        # Template selection
        template_layout = QHBoxLayout()
        template_label = QLabel("Template:")
        template_label.setMinimumWidth(120)
        self.template_combo = QComboBox()
        self.template_combo.addItems(["word-focus", "default"])
        self.template_combo.setCurrentText("word-focus")
        template_layout.addWidget(template_label)
        template_layout.addWidget(self.template_combo)
        layout.addLayout(template_layout)

        # Run button
        self.run_btn = QPushButton("Run Pycaps")
        self.run_btn.setMinimumHeight(50)
        self.run_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-size: 14px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.run_btn.clicked.connect(self.run_pycaps)
        layout.addWidget(self.run_btn)

        layout.addStretch()

    def browse_file(self):
        # Use native macOS file picker
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Video File",
            str(Path.home()),
            "Video Files (*.mov *.mp4 *.avi *.mkv);;All Files (*.*)",
            options=QFileDialog.Option.DontUseNativeDialog if sys.platform != 'darwin' else QFileDialog.Option(0)
        )
        if file_path:
            self.file_input.setText(file_path)

    def run_pycaps(self):
        file_path = self.file_input.text()

        if not file_path:
            QMessageBox.warning(self, "Error", "Please select a video file")
            return

        if not Path(file_path).exists():
            QMessageBox.warning(self, "Error", "Selected file does not exist")
            return

        self.close()

        subprocess.run([
            "pycaps", "render",
            "--input", file_path,
            "--whisper-model", self.model_combo.currentText(),
            "--template", self.template_combo.currentText(),
            "--lang", self.lang_combo.currentText(),
            "--transcription-preview"
        ])

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PycapsGUI()
    window.show()
    sys.exit(app.exec())

