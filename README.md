# pymsbt
A simple python library for reading and editing .msbt (Message Studio Binary Text) files, which is a file format created by Nintendo for use in their games. These files are used for localization and displaying text to the player. This library was created for batch-editing or reading msbt files to mod Nintendo games, such as with a translator api or regex expression. This could be used to create language translations that aren't officialy supported by the base game.

## Installation
```bash
pip install pymsbt
```

## Example usage
( Make sure to read the [wiki](https://github.com/p1gyy/pymsbt/wiki) for more information )
### Reading a msbt file
```python
from pymsbt.msbt_read import MSBTFile

msbt = MSBTFile("./msbt/ActorMsg/Attachment.msbt")

print(msbt.LBL1.labels)
print(msbt.TXT2.texts)
print(msbt.ATR1)
```

### Editing a msbt file (COMING SOON)
```python
from pymsbt.msbt_read import MSBTFile
from pymsbt.msbt_write import MSBTWriter

msbt = MSBTFile("./msbt/ActorMsg/Attachment.msbt")
msbt.TXT2.texts[0][0]['data'] = 'test' # see the wiki for more information about the structure of text data

write = MSBTWriter(msbt, "output.msbt")
print("Wrote msbt file to", write.filepath)
```

