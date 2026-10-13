#!/usr/bin/env python3
"""Check resource memory safeguards without downloading or building Qt."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
HELPER = ROOT / "Telegram/cmake/opengram_prepare_resources.cmake"
CMAKE = os.environ.get("CMAKE_COMMAND", "cmake")

PREAMBLE = r'''
cmake_minimum_required(VERSION 3.25)
project(ResourceRouting LANGUAGES CXX)
file(WRITE "${CMAKE_CURRENT_BINARY_DIR}/stub.cpp" "int resource_stub;\n")
add_library(Telegram STATIC "${CMAKE_CURRENT_BINARY_DIR}/stub.cpp")

function(mock_big_resources version output resource)
    get_filename_component(name "${resource}" NAME_WE)
    add_library(rcc_object_${name} OBJECT "${CMAKE_CURRENT_BINARY_DIR}/stub.cpp")
    set_source_files_properties("${resource}" PROPERTIES SKIP_AUTORCC ON)
    set(object "${CMAKE_CURRENT_BINARY_DIR}/qrc_${name}.o")
    set_source_files_properties("${object}" PROPERTIES GENERATED ON EXTERNAL_OBJECT ON)
    set(${output} "${object}" PARENT_SCOPE)
    set_property(GLOBAL APPEND PROPERTY ROUTED "${version}:${name}")
endfunction()
function(qt5_add_big_resources output resource)
    mock_big_resources(qt5 objects "${resource}")
    set(${output} "${objects}" PARENT_SCOPE)
endfunction()
function(qt6_add_big_resources output resource)
    mock_big_resources(qt6 objects "${resource}")
    set(${output} "${objects}" PARENT_SCOPE)
endfunction()

function(add_bundle name)
    set(path "${CMAKE_CURRENT_SOURCE_DIR}/${name}.qrc")
    file(WRITE "${path}" "<RCC/>\n")
    target_sources(Telegram PRIVATE "${path}")
endfunction()
function(assert_route expected)
    get_property(actual GLOBAL PROPERTY ROUTED)
    if(NOT "${actual}" STREQUAL "${expected}")
        message(FATAL_ERROR "Expected '${expected}', got '${actual}'")
    endif()
endfunction()
'''


class ResourceRouting(unittest.TestCase):
    def configure(self, body, *, windows=True, major=5, succeeds=True):
        with tempfile.TemporaryDirectory(prefix="opengram resource tests ") as tmp:
            source = Path(tmp) / "src"
            source.mkdir()
            (source / "CMakeLists.txt").write_text(
                PREAMBLE + f'\ninclude("{HELPER.as_posix()}")\n'
                + f'set(WIN32 {"TRUE" if windows else "FALSE"})\n'
                + f'set(QT_VERSION_MAJOR {major})\n' + body,
                encoding="utf-8",
            )
            result = subprocess.run(
                [CMAKE, "-S", str(source), "-B", str(Path(tmp) / "build")],
                capture_output=True, text=True,
            )
            self.assertEqual(result.returncode == 0, succeeds,
                result.stdout + result.stderr)
            return result.stdout + result.stderr

    def test_all_bundles_and_future_bundles_use_both_qt_versions(self):
        for major in (5, 6):
            with self.subTest(major=major):
                self.configure(r'''
add_bundle(animations)
add_bundle(emoji_1)
add_bundle(new_future_bundle)
file(WRITE "${CMAKE_CURRENT_BINARY_DIR}/models.qrc"
    "<RCC><qresource><file>not_baked_yet.binobj</file></qresource></RCC>")
target_sources(Telegram PRIVATE "${CMAKE_CURRENT_BINARY_DIR}/models.qrc")
opengram_prepare_resources(Telegram)
assert_route("qt${QT_VERSION_MAJOR}:animations;qt${QT_VERSION_MAJOR}:emoji_1;qt${QT_VERSION_MAJOR}:new_future_bundle;qt${QT_VERSION_MAJOR}:models")
foreach(name animations emoji_1 new_future_bundle models)
    get_target_property(disabled rcc_object_${name} DISABLE_PRECOMPILE_HEADERS)
    if(NOT disabled)
        message(FATAL_ERROR "Resource stub must not use the application PCH")
    endif()
endforeach()
# Calling the helper again must not register duplicate resource objects.
opengram_prepare_resources(Telegram)
assert_route("qt${QT_VERSION_MAJOR}:animations;qt${QT_VERSION_MAJOR}:emoji_1;qt${QT_VERSION_MAJOR}:new_future_bundle;qt${QT_VERSION_MAJOR}:models")
''', major=major)

    def test_existing_skip_flags_are_preserved(self):
        self.configure(r'''
add_bundle(manual)
add_bundle(excluded)
add_bundle(regular)
set_source_files_properties("${CMAKE_CURRENT_SOURCE_DIR}/manual.qrc"
    PROPERTIES SKIP_AUTORCC ON)
set_source_files_properties("${CMAKE_CURRENT_SOURCE_DIR}/excluded.qrc"
    PROPERTIES SKIP_AUTOGEN ON)
opengram_prepare_resources(Telegram)
assert_route("qt5:regular")
''')

    def test_non_windows_packaging_is_unchanged(self):
        for major in (5, 6):
            with self.subTest(major=major):
                self.configure(r'''
add_bundle(animations)
opengram_prepare_resources(Telegram)
assert_route("")
get_source_file_property(skip "${CMAKE_CURRENT_SOURCE_DIR}/animations.qrc" SKIP_AUTORCC)
if(skip)
    message(FATAL_ERROR "Non-Windows resource packaging changed")
endif()
''', windows=False, major=major)

    def test_duplicate_basenames_fail_with_actionable_error(self):
        output = self.configure(r'''
file(MAKE_DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}/one" "${CMAKE_CURRENT_SOURCE_DIR}/two")
add_bundle(one/same)
add_bundle(two/same)
opengram_prepare_resources(Telegram)
''', succeeds=False)
        self.assertIn("Use unique .qrc basenames", output)

    def test_ci_keeps_both_parallelism_limits_and_x64_host(self):
        text = (ROOT / ".github/workflows/build-windows.yml").read_text(encoding="utf-8")
        build = text.split("- name: Build opengram\n", 1)[1].split("\n      - name:", 1)[0]
        self.assertIn("_CL_: /MP2", build)
        self.assertRegex(build, r"cmake --build [^\n]+ --parallel 1 -- /p:PreferredToolArchitecture=x64")
        self.assertIn("needs: checks", text)
        self.assertIn("python3 tools/build/test_resources.py", text)

    def test_finalization_runs_after_generated_resources(self):
        text = (ROOT / "Telegram/CMakeLists.txt").read_text(encoding="utf-8")
        self.assertLess(text.index("include(cmake/generate_models.cmake)"),
            text.index("opengram_prepare_resources(Telegram)"))
        self.assertLess(text.index("include(cmake/qrhi_shaders.cmake)"),
            text.index("opengram_prepare_resources(Telegram)"))
        self.assertLess(text.index("opengram_prepare_resources(Telegram)"),
            text.index("target_prepare_qrc(Telegram)"))
        self.assertEqual(text.count("opengram_prepare_resources(Telegram)"), 1)


if __name__ == "__main__":
    unittest.main()
