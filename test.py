def get_quad(well_no, old_well_no, odd_even, pattern):
    # Check if well no 1-4 or 5-8 etc and continuous.
    if round((float(well_no)+1) / 4) % 2 == odd_even:
        pattern = 0
        start_of_part = True
        if odd_even == 0:
            odd_even = 1
        else:
            odd_even = 0
    elif old_well_no + 1 != well_no:
        pattern = 0
        start_of_part = True
    else:
        pattern += 1
        start_of_part = False
    return {'odd_even':odd_even,'pattern':pattern, 'start':start_of_part}

def gen_com(coord_file=None,
            coords=None,
            end_63x=None,
            stage_dict,
            job_list,
            pattern_list,
            pattern,
            first_job):

    # Lists for storing command strings.
    com_list = []
    end_com_list = []
    com = '/cli:1 /app:matrix /cmd:deletelist\n'
    end_com = ['/cli:1 /app:matrix /cmd:deletelist\n']

    if coord_file is None:
        coord_file = False
    if coords is None:
        coords = {}
    odd_even = 0
    dx = 0
    dy = 0
    if end_63x is None:
        end_63x = False
    #pattern = -1
    start_of_part = False
    fov_is = False
    prev_well = ''
    gain = ''
    #stage_dict = defaultdict()
    cstart = camstart_com()
    enable = 'true'

    #if stage3:
    #    print('Stage3')
        #stage_dict = green_sorted
        #pattern = 0
        #if end_10x:
        #    job_list = job_10x
        #    pattern_list = pattern_10x
        #elif end_40x:
        #    job_list = job_40x
        #    pattern_list = pattern_40x

    if end_63x:
        #print('Stage4')
        #channels = range(4)
        #stage_dict = wells
        old_well_no = stage_dict.items()[0][0] - 1
        #job_list = job_63x
        #fov_is = False
    for k, v in stage_dict.iteritems():
        if not end_63x:
            channels = [k,
                        medians['blue'],
                        medians['yellow'],
                        medians['red']
                        ]
        if end_63x:
            channels = [sec_gain_dict[v][0],
                        medians['blue'],
                        medians['yellow'],
                        medians['red']
                        ]
        if end_63x:
            result = get_quad(k, old_well_no, odd_even, pattern)
            pattern = result['pattern']
            start_of_part = result['start']
            #pattern_list = pattern_63x[pattern]
            old_well_no = k
        used_pattern = pattern_list[pattern]
        if start_of_part and fov_is:
            # Store the commands in lists, after one well at least.
            com_list.append(com)
            end_com_list.append(end_com)
            com = '/cli:1 /app:matrix /cmd:deletelist\n'
            fov_is = False
        elif start_of_part and not fov_is:
            # reset the com string
            com = '/cli:1 /app:matrix /cmd:deletelist\n'
        if not end_63x:
            start_of_part = True
            fov_is = True
        for i, c in enumerate(channels):
            gain = str(c)
            if i < 2:
                detector = '1'
                job = job_list[i + 3*pattern]
            if i >= 2:
                detector = '2'
                job = job_list[i - 1 + 3*pattern]
            com = com + gain_com(job, detector, gain) + '\n'
        for well in v:
            if end_63x:
                well = v
            if well != prev_well:
                prev_well = well
                for i in range(2):
                    for j in range(2):
                        if end_63x:
                            # Only enable selected wells from file (arg)
                            fov = '{}--X0{}--Y0{}'.format(well, j, i)
                            if coord_file and fov in coords.keys():
                                enable = 'true'
                                dx = coords[fov][0]
                                dy = coords[fov][1]
                                fov_is = True
                            elif not coord_file:
                                enable = 'true'
                                fov_is = True
                            else:
                                enable = 'false'
                        if enable == 'true' or not end_63x:
                            com = (com +
                                   enable_com(well,
                                              'X0{}--Y0{}'.format(j, i),
                                              enable
                                              ) +
                                   '\n' +
                                   # dx dy switched, scan rot -90 degrees
                                   cam_com(used_pattern,
                                           well,
                                           'X0{}--Y0{}'.format(j, i),
                                           str(dy),
                                           str(dx)
                                           ) +
                                   '\n')
                            end_com = ['CAM',
                                       well,
                                       'E0' + str(first_job + 2),
                                       'X0{}--Y0{}'.format(j, i)
                                       ]
    if fov_is:
        # Store the last unstored commands in lists, after one well at least.
        com_list.append(com)
        end_com_list.append(end_com)
