class WeaponType:
    """
    Enum representing different weapon types
    """
    KINETIC = 'Kinetic'
    ENERGY = 'Energy'
    POWER = 'Power'
    UNKNOWN = 'Unknown'

    # Used in a couple spots in the code, for determining if something is in a player's inventory
    # or is in the postmaster
    BUCKET_HASHES = [1498876634, 2465295065, 953998645]

    @staticmethod
    def get_type_from_bucket_hash(bucket_type_hash):
        """
        Convert from a bucket type hash to a weapon type. The bucket type hashes correspond to
        hashes used in the Destiny 2 API
        """
        return {
            WeaponType.BUCKET_HASHES[0]: WeaponType.KINETIC,
            WeaponType.BUCKET_HASHES[1]: WeaponType.ENERGY,
            WeaponType.BUCKET_HASHES[2]: WeaponType.POWER
        }.get(bucket_type_hash, WeaponType.UNKNOWN)

    @staticmethod
    def get_enum_from_string(sub_type_string):
        """
        Convert a weapon type string to a weapon type enum value. Used for parsing viewer chat
        input. Note that both power and heavy are valid, because viewers might use either term
        """
        # Remove all nonletters, and convert to lowercase
        sub_type_string = ''.join(ch for ch in sub_type_string if ch.isalpha()).lower()

        return {
            'kinetic': WeaponType.KINETIC,
            'energy': WeaponType.ENERGY,
            'power': WeaponType.POWER,
            'heavy': WeaponType.POWER
        }.get(sub_type_string, WeaponType.UNKNOWN)


class TierType:
    """
    Weapon tier type. Exotic is the only one used in the code at the moment
    """
    BASIC = 2
    COMMON = 3
    RARE = 4
    SUPERIOR = 5
    EXOTIC = 6


class WeaponSubType:
    """
    Enum representing different weapon subtypes. These values correspond to values used in the
    Destiny 2 API
    """
    AUTO_RIFLE = 6
    SHOTGUN = 7
    MACHINE_GUN = 8
    HAND_CANNON = 9
    ROCKET_LAUNCHER = 10
    FUSION_RIFLE = 11
    SNIPER_RIFLE = 12
    PULSE_RIFLE = 13
    SCOUT_RIFLE = 14
    SIDEARM = 17
    SWORD = 18
    LINEAR_FUSION_RIFLE = 22
    GRENADE_LAUNCHER = 23
    SUBMACHINE_GUN = 24
    TRACE_RIFLE = 25
    BOW = 31
    UNKNOWN = 0

    @staticmethod
    def get_string_representation(sub_type):
        """
        Get a user-friendly string representation of the weapon subtype
        """
        return {
            WeaponSubType.AUTO_RIFLE: 'Auto Rifle',
            WeaponSubType.SHOTGUN: 'Shotgun',
            WeaponSubType.MACHINE_GUN: 'Machine Gun',
            WeaponSubType.HAND_CANNON: 'Hand Cannon',
            WeaponSubType.ROCKET_LAUNCHER: 'Rocket Launcher',
            WeaponSubType.FUSION_RIFLE: 'Fusion Rifle',
            WeaponSubType.SNIPER_RIFLE: 'Sniper Rifle',
            WeaponSubType.PULSE_RIFLE: 'Pulse Rifle',
            WeaponSubType.SCOUT_RIFLE: 'Scout Rifle',
            WeaponSubType.SIDEARM: 'Sidearm',
            WeaponSubType.SWORD: 'Sword',
            WeaponSubType.LINEAR_FUSION_RIFLE: 'Linear Fusion Rifle',
            WeaponSubType.GRENADE_LAUNCHER: 'Grenade Launcher',
            WeaponSubType.SUBMACHINE_GUN: 'Submachine Gun',
            WeaponSubType.TRACE_RIFLE: 'Trace Rifle',
            WeaponSubType.BOW: 'Bow'
        }.get(sub_type, 'Unknown')

    @staticmethod
    def get_enum_from_string(sub_type_string):
        """
        Convert a weapon subtype string to a weapon subtype enum value. Used for parsing viewer chat
        input. Some abbreviated forms are permitted
        """
        # Remove all nonletters, and convert to lowercase
        sub_type_string = ''.join(ch for ch in sub_type_string if ch.isalpha()).lower()

        return {
            'autorifle': WeaponSubType.AUTO_RIFLE,
            'auto': WeaponSubType.AUTO_RIFLE,
            'shotgun': WeaponSubType.SHOTGUN,
            'machinegun': WeaponSubType.MACHINE_GUN,
            'handcannon': WeaponSubType.HAND_CANNON,
            'rocketlauncher': WeaponSubType.ROCKET_LAUNCHER,
            'fusionrifle': WeaponSubType.FUSION_RIFLE,
            'fusion': WeaponSubType.FUSION_RIFLE,
            'sniperrifle': WeaponSubType.SNIPER_RIFLE,
            'sniper': WeaponSubType.SNIPER_RIFLE,
            'pulserifle': WeaponSubType.PULSE_RIFLE,
            'pulse': WeaponSubType.PULSE_RIFLE,
            'scoutrifle': WeaponSubType.SCOUT_RIFLE,
            'scout': WeaponSubType.SCOUT_RIFLE,
            'sidearm': WeaponSubType.SIDEARM,
            'sword': WeaponSubType.SWORD,
            'linearfusionrifle': WeaponSubType.LINEAR_FUSION_RIFLE,
            'linearfusion': WeaponSubType.LINEAR_FUSION_RIFLE,
            'grenadelauncher': WeaponSubType.GRENADE_LAUNCHER,
            'submachinegun': WeaponSubType.SUBMACHINE_GUN,
            'smg': WeaponSubType.SUBMACHINE_GUN,
            'tracerifle': WeaponSubType.TRACE_RIFLE,
            'bow': WeaponSubType.BOW
        }.get(sub_type_string, WeaponSubType.UNKNOWN)
