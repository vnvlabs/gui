

try:
    import app.models.VnVFile as VnVFile_
    VnVFile = VnVFile_
    VnVFileActive = True
except:
    VnVFileActive = False
    VnVFile = None