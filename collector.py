import traceback

import console

def main():
    try:
        pass
    except Exception as e:
        console.print(traceback.format_exc())
        console.print("程序出现未知错误，请联系监考员\n", 'red')

if __name__ == '__main__':
    console.start('Code Collector', main)
