import pytest
import pkg_resources
import shutil
import time
from os.path import join as pjoin


from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog, QFileDialog


from funiilabel import funiilabel


@pytest.fixture
def window(qtbot):
    """Pass the application to the test functions via a pytest fixture."""
    new_window = funiilabel.FuniiLabel()
    qtbot.add_widget(new_window)
    new_window.show()
    yield new_window
    if pkg_resources.resource_isdir("tests.test_video", "label"):
        vid_folder = pkg_resources.resource_filename(
                "tests.test_video", "label"
            )
        shutil.rmtree(vid_folder)
    return



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
    vid_path = pkg_resources.resource_filename(
            "tests.test_video", "vid.mp4"
        )
    mock.patch.object(QFileDialog, 'getOpenFileName', return_value=(vid_path, 1))
    qtbot.keyClick(window.file_sub_menu, Qt.Key_Enter)
    for _ in  range(10):
        qtbot.keyPress(window, Qt.Key_F)
    for _ in  range(10):
        qtbot.keyPress(window, Qt.Key_E)
    for _ in  range(10):
        qtbot.keyPress(window, Qt.Key_S)
    for _ in  range(10):
        qtbot.keyPress(window, Qt.Key_O)
    
    qtbot.keyClick(window.file_sub_menu, Qt.Key_Down)
    qtbot.keyClick(window.file_sub_menu, Qt.Key_Down)
    qtbot.keyClick(window.file_sub_menu, Qt.Key_Down)

    mock.patch.object(QFileDialog, 'getOpenFileName', return_value=(vid_path, 1))
    qtbot.keyClick(window.file_sub_menu, Qt.Key_Enter)
    while not window.label_recorder_process.label_queue.empty():
        # wait for recording to process
        time.sleep(0.1)

    assert pkg_resources.resource_exists(
            "tests.test_video", pjoin("label","vid_frame_40_label_Other.jpeg")
        )
    assert not pkg_resources.resource_exists(
            "tests.test_video", pjoin("label","vid_frame_41_label_Other.jpeg")
        )
    assert pkg_resources.resource_exists(
            "tests.test_video", pjoin("label","vid.txt")
        )


def test_about_dialog(window, qtbot, mock):
    """Test the About item of the Help submenu.

    Qtbot clicks on the help sub menu and then navigates to the About item. Mock creates
    a QDialog object to be used for the test.
    """
    qtbot.mouseClick(window.help_sub_menu, Qt.LeftButton)
    qtbot.keyClick(window.help_sub_menu, Qt.Key_Down)
    mock.patch.object(QDialog, 'exec_', return_value='accept')
    qtbot.keyClick(window.help_sub_menu, Qt.Key_Enter)
