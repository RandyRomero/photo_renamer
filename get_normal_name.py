#!python3
# -*- coding: utf-8 -*-


def get_normal_name(camera_brand, camera_model, lens_brand, lens_model):
    # Convert code names to meaningful names

    # Nobody cares whether Nikon is a corporation or whatever
    if camera_brand == 'NIKON CORPORATION':
        camera_brand = 'NIKON'

    if camera_brand == 'motorola':
        camera_brand = 'Motorola'

    if camera_model == 'Redmi Note3':
        camera_model = 'Redmi Note 3 Pro'

    if camera_model in ['G8342', 'G8341', 'G8343']:
        camera_model = 'Xperia XZ1'

    if camera_model == 'chiron':
        camera_model = 'Mi Mix 2'

    if camera_model == 'Moto G (5S)':
        camera_model = 'Moto G5S'

    if camera_model == 'CPH1707':
        camera_model = 'R11'

    return camera_brand, camera_model, lens_brand, lens_model
