# This file is part of Telegram Desktop,
# the official desktop application for the Telegram messaging service.
#
# For license and copyright information please follow this link:
# https://github.com/telegramdesktop/tdesktop/blob/master/LEGAL

function(opengram_prepare_resources target_name)
    if (NOT WIN32)
        return()
    endif()

    # Scan after all sources are registered, including generated models/shaders.
    get_target_property(resource_sources ${target_name} SOURCES)
    foreach(resource_file IN LISTS resource_sources)
        if (NOT resource_file MATCHES "\\.qrc$")
            continue()
        endif()
        get_source_file_property(skip_autogen "${resource_file}" SKIP_AUTOGEN)
        get_source_file_property(skip_autorcc "${resource_file}" SKIP_AUTORCC)
        if (skip_autogen OR skip_autorcc)
            continue()
        endif()

        # Qt 5 names its object targets by basename, not by the .qrc path.
        get_filename_component(resource_name "${resource_file}" NAME_WE)
        if (TARGET rcc_object_${resource_name})
            message(FATAL_ERROR
                "Duplicate big-resource name '${resource_name}' for ${resource_file}. "
                "Use unique .qrc basenames to avoid Qt object-target collisions.")
        endif()

        set(resource_objects)
        if (QT_VERSION_MAJOR GREATER_EQUAL 6)
            qt6_add_big_resources(resource_objects "${resource_file}")
        else()
            qt5_add_big_resources(resource_objects "${resource_file}")
        endif()
        # Only the tiny registration stub is compiled; rcc inserts the payload.
        set_target_properties(rcc_object_${resource_name} PROPERTIES
            DISABLE_PRECOMPILE_HEADERS ON
        )
        target_sources(${target_name} PRIVATE ${resource_objects})
    endforeach()
endfunction()
