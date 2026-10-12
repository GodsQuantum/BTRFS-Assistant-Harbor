cmake_minimum_required(VERSION 3.16)

project(btrfs-assistant-harbor VERSION 0.1.0 LANGUAGES CXX)

include(GNUInstallDirs)

set(CMAKE_INCLUDE_CURRENT_DIR ON)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

set(CMAKE_AUTOUIC ON)
set(CMAKE_AUTOMOC ON)
set(CMAKE_AUTORCC ON)
set_directory_properties(PROPERTIES CLEAN_NO_CUSTOM 1)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

set(CMAKE_AUTOUIC_SEARCH_PATHS src/ui)

find_package(QT NAMES Qt6 COMPONENTS Widgets LinguistTools REQUIRED)
find_package(Qt${QT_VERSION_MAJOR} COMPONENTS Widgets LinguistTools REQUIRED)

add_subdirectory(src)
add_subdirectory(icons)

message(STATUS "Btrfs Assistant will be built for install into ${CMAKE_INSTALL_PREFIX}")

enable_testing()
add_executable(test-remote-backup-plan
    tests/test_remote_plan.cpp src/util/RemoteBackupPlan.cpp)
target_include_directories(test-remote-backup-plan PRIVATE src)
target_link_libraries(test-remote-backup-plan PRIVATE Qt6::Core)
add_test(NAME remote-backup-plan COMMAND test-remote-backup-plan)
