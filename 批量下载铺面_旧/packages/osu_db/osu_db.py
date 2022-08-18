import json

from . import buffer


def read_osu_db(filepath: str) -> dict:
    """读取osu_db并返回, 一次使用一次读, 多次使用请重写"""
    with open(filepath, "rb") as db:
        version = buffer.read_uint(db)
        folder_count = buffer.read_uint(db)
        account_unlocked = buffer.read_bool(db)

        # skip this datetime shit for now (8 bytes)
        buffer.read_uint(db)
        buffer.read_uint(db)

        name = buffer.read_string(db)
        num_beatmaps = buffer.read_uint(db)

        db_info = {
            'version': version,
            'folder_count': folder_count,
            'account_unlocked': account_unlocked,
            'name': name,
            'num_beatmaps': num_beatmaps,
            'beatmaps': []
        }

        for _ in range(num_beatmaps):
            artist = buffer.read_string(db)
            artist_unicode = buffer.read_string(db)
            song_title = buffer.read_string(db)
            song_title_unicode = buffer.read_string(db)
            mapper = buffer.read_string(db)
            difficulty = buffer.read_string(db)
            audio_file = buffer.read_string(db)
            md5_hash = buffer.read_string(db)
            map_file = buffer.read_string(db)
            ranked_status = buffer.read_ubyte(db)
            num_hitcircles = buffer.read_ushort(db)
            num_sliders = buffer.read_ushort(db)
            num_spinners = buffer.read_ushort(db)
            last_modified = buffer.read_ulong(db)
            approach_rate = buffer.read_float(db)
            circle_size = buffer.read_float(db)
            hp_drain = buffer.read_float(db)
            overall_difficulty = buffer.read_float(db)
            slider_velocity = buffer.read_double(db)

            # skip these int double pairs, personally i dont think they're
            # important for the purpose of this database
            i = buffer.read_uint(db)
            for _ in range(i):
                buffer.read_int_double(db)

            i = buffer.read_uint(db)
            for _ in range(i):
                buffer.read_int_double(db)

            i = buffer.read_uint(db)
            for _ in range(i):
                buffer.read_int_double(db)

            i = buffer.read_uint(db)
            for _ in range(i):
                buffer.read_int_double(db)

            drain_time = buffer.read_uint(db)
            total_time = buffer.read_uint(db)
            preview_time = buffer.read_uint(db)

            # skip timing points
            # i = buffer.read_uint(db)
            for _ in range(buffer.read_uint(db)):
                buffer.read_timing_point(db)

            beatmap_id = buffer.read_uint(db)
            beatmap_set_id = buffer.read_uint(db)
            thread_id = buffer.read_uint(db)
            grade_standard = buffer.read_ubyte(db)
            grade_taiko = buffer.read_ubyte(db)
            grade_ctb = buffer.read_ubyte(db)
            grade_mania = buffer.read_ubyte(db)
            local_offset = buffer.read_ushort(db)
            stack_leniency = buffer.read_float(db)
            gameplay_mode = buffer.read_ubyte(db)
            song_source = buffer.read_string(db)
            song_tags = buffer.read_string(db)
            online_offset = buffer.read_ushort(db)
            title_font = buffer.read_string(db)
            is_unplayed = buffer.read_bool(db)
            last_played = buffer.read_ulong(db)
            is_osz2 = buffer.read_bool(db)
            folder_name = buffer.read_string(db)
            last_checked = buffer.read_ulong(db)
            ignore_sounds = buffer.read_bool(db)
            ignore_skin = buffer.read_bool(db)
            disable_storyboard = buffer.read_bool(db)
            disable_video = buffer.read_bool(db)
            visual_override = buffer.read_bool(db)
            last_modified2 = buffer.read_uint(db)
            scroll_speed = buffer.read_ubyte(db)

            db_info['beatmaps'].append(
                {
                    'artist': artist,
                    'artist_unicode': artist_unicode,
                    'song_title': song_title,
                    'song_title_unicode': song_title_unicode,
                    'mapper': mapper,
                    'difficulty': difficulty,
                    'audio_file': audio_file,
                    'md5_hash': md5_hash,
                    'map_file': map_file,
                    'ranked_status': ranked_status,
                    'num_hitcircles': num_hitcircles,
                    'num_sliders': num_sliders,
                    'num_spinners': num_spinners,
                    'last_modified': last_modified,
                    'approach_rate': approach_rate,
                    'circle_size': circle_size,
                    'hp_drain': hp_drain,
                    'overall_difficulty': overall_difficulty,
                    'slider_velocity': slider_velocity,
                    'drain_time': drain_time,
                    'total_time': total_time,
                    'preview_time': preview_time,
                    'beatmap_id': beatmap_id,
                    'beatmap_set_id': beatmap_set_id,
                    'thread_id': thread_id,
                    'grade_standard': grade_standard,
                    'grade_taiko': grade_taiko,
                    'grade_ctb': grade_ctb,
                    'grade_mania': grade_mania,
                    'local_offset': local_offset,
                    'stack_leniency': stack_leniency,
                    'gameplay_mode': gameplay_mode,
                    'song_source': song_source,
                    'song_tags': song_tags,
                    'online_offset': online_offset,
                    'title_font': title_font,
                    'is_unplayed': is_unplayed,
                    'last_played': last_played,
                    'is_osz2': is_osz2,
                    'folder_name': folder_name,
                    'last_checked': last_checked,
                    'ignore_sounds': ignore_sounds,
                    'ignore_skin': ignore_skin,
                    'disable_storyboard': disable_storyboard,
                    'disable_video': disable_video,
                    'visual_override': visual_override,
                    'last_modified2': last_modified2,
                    'scroll_speed': scroll_speed
                }
            )
    return db_info


def main():
    info = read_osu_db(r"C:\Users\abbey\AppData\Local\osu!\osu!.db")
    with open('../../../Examples/osu_db.json', 'w') as f:
        f.write(json.dumps(info))


if __name__ == '__main__':
    main()
