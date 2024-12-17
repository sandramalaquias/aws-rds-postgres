import os
import rebuild
import load

def handler(event, context):
    if 'local' in event:
        df, db_config = load.getDataLocal()
    else:
        db_config = rebuild.getRDS()
        df = load.getDataURL()

    rebuild.rebuildTables(db_config)
    load.pipeline(db_config, df)

if __name__ == "__main__":
    context = {}
    event = {'local' : True}
    handler(event, context)


