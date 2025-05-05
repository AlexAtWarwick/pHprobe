from ORION_driver import OrionControl, OrionError

if __name__ == "__main__":
    try:
        with OrionControl(port="COM11") as meter:
            result = meter.get_measurement()
            if result:
                print(result)
    except OrionError as e:
        print(f"Meter error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")
