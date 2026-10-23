install(FILES btrfs-assistant-harbor.svg DESTINATION ${CMAKE_INSTALL_DATAROOTDIR}/icons/hicolor/scalable/apps/)

# Circular branded icon shipped at native launcher sizes.
foreach(harbor_size 16 24 32 48 64 128 256 512)
    install(FILES "${CMAKE_CURRENT_SOURCE_DIR}/hicolor/harbor-icon-${harbor_size}.png"
            DESTINATION "${CMAKE_INSTALL_DATAROOTDIR}/icons/hicolor/${harbor_size}x${harbor_size}/apps"
            RENAME "btrfs-assistant-harbor.png")
endforeach()
