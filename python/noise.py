import cv2 as cv
from time import time
from PySide2.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QCheckBox,
    QLabel,
    QVBoxLayout,
    QSpinBox)

from tools import ToolWidget
from utility import create_lut, elapsed_time
from viewer import ImageViewer


class NoiseWidget(ToolWidget):
    def __init__(self, image, parent=None):
        super(NoiseWidget, self).__init__(parent)

        params_layout = QHBoxLayout()
        params_layout.addWidget(QLabel(self.tr('Mode:')))
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(
            [self.tr('Median'), self.tr('Gaussian'), self.tr('BoxBlur'), self.tr('Bilateral'), self.tr('NonLocal')])
        params_layout.addWidget(self.mode_combo)

        params_layout.addWidget(QLabel(self.tr('Radius:')))
        self.radius_spin = QSpinBox()
        self.radius_spin.setRange(1, 10)
        self.radius_spin.setSuffix(self.tr(' px'))
        self.radius_spin.setValue(1)
        params_layout.addWidget(self.radius_spin)

        params_layout.addWidget(QLabel(self.tr('Sigma:')))
        self.sigma_spin = QSpinBox()
        self.sigma_spin.setRange(1, 200)
        self.sigma_spin.setValue(3)
        params_layout.addWidget(self.sigma_spin)

        params_layout.addWidget(QLabel(self.tr('Levels:')))
        self.levels_spin = QSpinBox()
        self.levels_spin.setRange(-1, 255)
        self.levels_spin.setSpecialValueText(self.tr('Auto'))
        self.levels_spin.setValue(-1)
        params_layout.addWidget(self.levels_spin)

        self.equalize_check = QCheckBox(self.tr('Equalized'))
        params_layout.addWidget(self.equalize_check)
        self.gray_check = QCheckBox(self.tr('Grayscale'))
        params_layout.addWidget(self.gray_check)
        self.denoised_check = QCheckBox(self.tr('Denoised'))
        params_layout.addWidget(self.denoised_check)
        params_layout.addStretch()

        self.image = image
        self.viewer = ImageViewer(self.image, self.image)
        self.process()

        main_layout = QVBoxLayout()
        main_layout.addLayout(params_layout)
        main_layout.addWidget(self.viewer)
        self.setLayout(main_layout)

        self.mode_combo.currentTextChanged.connect(self.process)
        self.radius_spin.valueChanged.connect(self.process)
        self.sigma_spin.valueChanged.connect(self.process)
        self.levels_spin.valueChanged.connect(self.process)
        self.equalize_check.stateChanged.connect(self.process)
        self.gray_check.stateChanged.connect(self.process)
        self.denoised_check.stateChanged.connect(self.process)

    def process(self):
        start = time()
        grayscale = self.gray_check.isChecked()
        if grayscale:
            original = cv.cvtColor(self.image, cv.COLOR_BGR2GRAY)
        else:
            original = self.image
        radius = self.radius_spin.value()
        kernel = radius*2 + 1
        sigma = self.sigma_spin.value()
        choice = self.mode_combo.currentText()
        if choice == self.tr('Median'):
            self.sigma_spin.setEnabled(False)
            denoised = cv.medianBlur(original, kernel)
        elif choice == self.tr('Gaussian'):
            self.sigma_spin.setEnabled(False)
            denoised = cv.GaussianBlur(original, (kernel, kernel), 0)
        elif choice == self.tr('BoxBlur'):
            self.sigma_spin.setEnabled(False)
            denoised = cv.blur(original, (kernel, kernel))
        elif choice == self.tr('Bilateral'):
            self.sigma_spin.setEnabled(True)
            denoised = cv.bilateralFilter(original, kernel, sigma, sigma)
        elif choice == self.tr('NonLocal'):
            if grayscale:
                denoised = cv.fastNlMeansDenoising(original, None, kernel)
            else:
                denoised = cv.fastNlMeansDenoisingColored(original, None, kernel, kernel)
        else:
            denoised = None

        if self.denoised_check.isChecked():
            self.levels_spin.setEnabled(False)
            self.equalize_check.setEnabled(False)
            result = denoised
        else:
            self.levels_spin.setEnabled(True)
            self.equalize_check.setEnabled(True)
            noise = cv.absdiff(original, denoised)
            if self.equalize_check.isChecked():
                self.levels_spin.setEnabled(False)
                if grayscale:
                    result = cv.equalizeHist(noise)
                else:
                    result = cv.merge([cv.equalizeHist(c) for c in cv.split(noise)])
            else:
                self.levels_spin.setEnabled(True)
                high = self.levels_spin.value()
                if high == -1:
                    noise = cv.normalize(noise, None, 0, 255, cv.NORM_MINMAX)
                else:
                    high = max(1, high)
                    noise = cv.LUT(noise, create_lut(0, 255 - high))
                result = noise
        if grayscale:
            result = cv.cvtColor(result, cv.COLOR_GRAY2BGR)
        self.viewer.update_processed(result)
        self.info_message.emit(self.tr('Noise estimation = {}'.format(elapsed_time(start))))