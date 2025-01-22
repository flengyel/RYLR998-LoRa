if __name__ == "__main__":
    import re # regular expressions for argument checking
    from src.ui.constants import (RadioDefaults, RadioLimits)
    from src.config.validators import (
        bandcheck, pwrcheck, modecheck, netidcheck, uartcheck,
         paramcheck, validate_netid_parameter
    )

 
    # Get args from new parser
    from src.config.parser import parse_args
    args = parse_args()
    
    # Apply all validation functions to the args
    args.band = bandcheck(args.band)
    if args.pwr is not None:
        args.pwr = pwrcheck(args.pwr)
    args.mode = modecheck(args.mode)  
    args.netid = netidcheck(args.netid)
    args.port = uartcheck(args.port)

     # Parameter validation including netid check
    validate_netid_parameter(args.netid, args.parameter)
    args.parameter = paramcheck(args.parameter)

    rylr  = rylr998(args)
    try:
        asyncio.run(cur.wrapper(rylr.xcvr))
    except KeyboardInterrupt:
        pass
    finally:
        print("73!")