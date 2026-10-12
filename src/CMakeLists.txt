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

qt6_create_translation(FILES_TS ${PROJECT_SOURCE_DIR}/src ${TS_FILES})

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
