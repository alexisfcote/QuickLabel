import pytest

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog, QFileDialog

from funiilabel import FuniiLabel


@pytest.fixture
def window(qtbot):
    """Pass the application to the test functions via a pytest fixture."""
    new_window = FuniiLabel.FuniiLabel()
    qtbot.add_widget(new_window)
    new_window.show()
    return new_window


def test_window_title(window):
    """Check that the window title shows as declared."""
    assert window.windowTitle() == 'FuniiLabel'



def test_open_file(window, qtbot, mock):
    """Test the Open File item of the File submenu.

    Qtbot clicks on the file sub menu and then navigates to the Open File item. Mock creates
    an object to be passed to the QFileDialog.
    """
    qtbot.mouseClick(window.file_sub_menu, Qt.LeftButton)
    qtbot.keyClick(window.file_sub_menu, Qt.Key_Down)
    mock.patch.object(QFileDialog, 'getOpenFileName', return_value=('', ''))
    qtbot.keyClick(window.file_sub_menu, Qt.Key_Enter)


def test_about_dialog(window, qtbot, mock):
    """Test the About item of the Help submenu.

    Qtbot clicks on the help sub menu and then navigates to the About item. Mock creates
    a QDialog object to be used for the test.
    """
    qtbot.mouseClick(window.help_sub_menu, Qt.LeftButton)
    qtbot.keyClick(window.help_sub_menu, Qt.Key_Down)
    mock.patch.object(QDialog, 'exec_', return_value='accept')
    qtbot.keyClick(window.help_sub_menu, Qt.Key_Enter)
