include(ui/CMakeLists.txt)
include(model/CMakeLists.txt)
include(util/CMakeLists.txt)
include(widgets/CMakeLists.txt)

set_property(SOURCE main.cpp APPEND PROPERTY COMPILE_DEFINITIONS "VERSION=\"1.5\"")

set(btrfsassistant_SRCS
    main.cpp
    ${UI_SRC}
    ${MODEL_SRC}
    ${UTIL_SRC}
    ${WIDGETS_SRC}
    ${PROJECT_SOURCE_DIR}/icons/icons.qrc
)

file(GLOB TS_FILES ${PROJECT_SOURCE_DIR}/translations/*.ts)

# Build reviewed translations with the imported Qt6 lrelease tool. The API of
# qt6_add_lrelease changed across Qt 6.4/6.8/6.10, so use explicit output rules
# that remain compatible with all three distributions. Never run lupdate.
if(TARGET Qt6::lrelease)
    set(HARBOR_LRELEASE "$<TARGET_FILE:Qt6::lrelease>")
else()
    find_program(HARBOR_LRELEASE NAMES lrelease-qt6 lrelease6 lrelease REQUIRED)
endif()
set(FILES_TS)
foreach(TS_FILE IN LISTS TS_FILES)
    get_filename_component(TS_BASENAME "${TS_FILE}" NAME_WE)
    set(QM_FILE "${CMAKE_CURRENT_BINARY_DIR}/${TS_BASENAME}.qm")
    add_custom_command(
        OUTPUT "${QM_FILE}"
        COMMAND "${HARBOR_LRELEASE}" "${TS_FILE}" -qm "${QM_FILE}"
        DEPENDS "${TS_FILE}"
        COMMENT "Compile reviewed translation ${TS_BASENAME}"
        VERBATIM)
    list(APPEND FILES_TS "${QM_FILE}")
endforeach()
add_custom_target(btrfs-assistant-harbor_lrelease ALL DEPENDS ${FILES_TS})

add_executable(btrfs-assistant-harbor-bin
    ${btrfsassistant_SRCS} ${FILES_TS}
)

install(FILES ${FILES_TS} DESTINATION ${CMAKE_INSTALL_DATAROOTDIR}/btrfs-assistant-harbor/translations)
install(FILES btrfs-assistant-harbor.desktop DESTINATION ${CMAKE_INSTALL_DATAROOTDIR}/applications)
install(FILES btrfs-assistant-harbor.metainfo.xml DESTINATION ${CMAKE_INSTALL_DATAROOTDIR}/metainfo)
install(FILES org.btrfs-assistant-harbor.pkexec.policy DESTINATION ${CMAKE_INSTALL_DATAROOTDIR}/polkit-1/actions/)
install(PROGRAMS btrfs-assistant-harbor DESTINATION ${CMAKE_INSTALL_BINDIR})
install(PROGRAMS btrfs-assistant-harbor-launcher DESTINATION ${CMAKE_INSTALL_BINDIR})
install(TARGETS btrfs-assistant-harbor-bin RUNTIME DESTINATION ${CMAKE_INSTALL_BINDIR})
install(PROGRAMS ${PROJECT_SOURCE_DIR}/backend/remote_schedule.py
        DESTINATION ${CMAKE_INSTALL_BINDIR}
        RENAME btrfs-assistant-harbor-schedule)

find_library(BTRFSUTIL_LIB btrfsutil)
target_link_libraries(btrfs-assistant-harbor-bin PRIVATE Qt${QT_VERSION_MAJOR}::Widgets ${BTRFSUTIL_LIB})
target_compile_options(btrfs-assistant-harbor-bin PRIVATE -Wall -Wextra -Wconversion)

# Non-destructive user GUI test: no Snapper repo or destructive actions.
find_package(Qt6 COMPONENTS Test REQUIRED)
add_executable(test-harbor-gui-user-smoke
    ${PROJECT_SOURCE_DIR}/tests/test_gui_user_smoke.cpp
    ${UI_SRC} ${MODEL_SRC} ${UTIL_SRC} ${WIDGETS_SRC}
    ${PROJECT_SOURCE_DIR}/icons/icons.qrc)
target_include_directories(test-harbor-gui-user-smoke PRIVATE ${PROJECT_SOURCE_DIR}/src)
# The GUI smoke test includes ui_MainWindow.h from tests/, unlike MainWindow.cpp.
# Resolve the original Designer file from its canonical source directory.
set_target_properties(test-harbor-gui-user-smoke PROPERTIES
    AUTOUIC_SEARCH_PATHS "${PROJECT_SOURCE_DIR}/src/ui")
target_link_libraries(test-harbor-gui-user-smoke PRIVATE Qt6::Widgets Qt6::Test ${BTRFSUTIL_LIB})
add_test(NAME gui-user-workflow-smoke
         COMMAND ${CMAKE_COMMAND} -E env QT_QPA_PLATFORM=offscreen
                 $<TARGET_FILE:test-harbor-gui-user-smoke>)


if(CMAKE_BUILD_TYPE STREQUAL "Debug")
    target_compile_options(btrfs-assistant-harbor-bin PRIVATE -Werror)
endif()

# Preserve legacy snapshot-v2 archives without hijacking btrfs-backup-ng.
install(DIRECTORY ${PROJECT_SOURCE_DIR}/vendor/harbor-legacy/btrfs_backup_ng
        DESTINATION lib/btrfs-assistant-harbor/legacy-python
        PATTERN "__pycache__" EXCLUDE PATTERN "*.pyc" EXCLUDE)
install(PROGRAMS ${PROJECT_SOURCE_DIR}/backend/harbor-checkpoint-v2
        DESTINATION ${CMAKE_INSTALL_BINDIR})
install(FILES ${PROJECT_SOURCE_DIR}/vendor/harbor-legacy/LICENSE-MIT
        DESTINATION ${CMAKE_INSTALL_DATAROOTDIR}/licenses/btrfs-assistant-harbor)


# CAS scheduler shared by the root-owned systemd profile runner.
install(FILES ${PROJECT_SOURCE_DIR}/backend/cas_schedule.py
        DESTINATION ${CMAKE_INSTALL_BINDIR})
