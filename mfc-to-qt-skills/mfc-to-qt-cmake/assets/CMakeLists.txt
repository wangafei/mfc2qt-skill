cmake_minimum_required(VERSION 3.19)

project(MyMfcPort LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

set(CMAKE_AUTOMOC ON)
set(CMAKE_AUTOUIC ON)
set(CMAKE_AUTORCC ON)

# ---------------------------------------------------------------------------
# Qt version: keep in sync with <project-root>/.mfc-qt/config.json
#   qt.resolvedMajor = 5 or 6
#   qt.minVersion    = e.g. 5.15 (used only for Qt 5)
#   qt.components    = Widgets, Network, Sql, ...
# ---------------------------------------------------------------------------
set(MFC_QT_MAJOR 6)          # <-- set to 5 for Qt 5 projects

if(MFC_QT_MAJOR EQUAL 6)
    find_package(Qt6 REQUIRED COMPONENTS Widgets)   # add more components here
    set(MFC_QT_WIDGETS Qt6::Widgets)
else()
    find_package(Qt5 5.15 REQUIRED COMPONENTS Widgets)
    set(MFC_QT_WIDGETS Qt5::Widgets)
endif()

add_executable(MyApp
    main.cpp
    mainwindow.h
    mainwindow.cpp
    mainwindow.ui
    logindialog.h
    logindialog.cpp
    logindialog.ui
    resources/app.qrc
)

target_include_directories(MyApp PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}/src
)

target_link_libraries(MyApp PRIVATE
    ${MFC_QT_WIDGETS}
)
