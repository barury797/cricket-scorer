from scorer import command 
import sys
sender = 'rizu titans ⚔️'

if len(sys.argv) == 2:
    print('Minified mode activated. Now all commands where the type is not specified will start with', sys.argv[1])

while True:
    text = input('Command: ')
    if text.startswith('.c '): 
        print(command(sender, 'c', text.replace('.c ', '')))
    elif text.startswith('.hc'):
        print(command(sender, 'hc', text.replace('.hc', '')))
    elif len(sys.argv) == 2:
        print(command(sender, sys.argv[1].replace('.', ''), text))

        