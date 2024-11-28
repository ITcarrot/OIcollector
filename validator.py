import traceback

import console

def main():
    try:
        x = 1 / 0
    except Exception as e:
        console.print(traceback.format_exc())
        console.print("程序出现未知错误，请联系考点负责人\n", 'red')

if __name__ == '__main__':
    console.start('System Validator', main)
