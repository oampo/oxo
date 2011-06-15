#! /usr/bin/env python
import sys
import os.path
import re

import pystache
from pygments import highlight
from pygments.lexers import JavascriptLexer
from pygments.formatters import HtmlFormatter

class OXO:
    def __init__(self):
        # Input files
        if len(sys.argv) < 3:
            exit()
        fileNames = sys.argv[1:-1]
        fileNames = [fileName for fileName in fileNames
                     if os.path.isfile(fileName)]

        files = []
        for fileName in fileNames:
            files.append(OXOFile(fileName))

        outFile = open(sys.argv[-1], 'w')
        outFile.write(View(files).render())
        outFile.close()

class View(pystache.View):
    template_name = "oxo"
    def __init__(self, files):
        pystache.View.__init__(self)
        self.fileList = []
        for file in files:
            fileDict = {}
            self.fileList.append(fileDict)

            fileDict["name"] = file.name
            fileDict["fileName"] = file.fileName

            fileDict["content"] = []
            for section in file.content:
                sectionDict = {}
                fileDict["content"].append(sectionDict)

                sectionDict["code"] = section["code"].formatted()

                commentDict = {}
                sectionDict["comment"] = commentDict

                comment = section["comment"]
                commentDict["body"] = comment.formatted()
                commentDict["tag"] = []

                for tag in comment.tags:
                    tagDict = {}
                    commentDict["tag"].append(tagDict)
                    tagDict["name"] = tag.name
                    tagDict["body"] = tag.body
                    
    def file(self):
        return self.fileList
        
class OXOFile:
    def __init__(self, fileName):
        self.fileName = fileName
        self.name = os.path.basename(fileName)
        self.name = os.path.splitext(self.name)[0]
        self.name = self.name.capitalize()

        jsFile = open(fileName, 'r')
        text = jsFile.read()
        self.content = []

        self.parse(text)

    def parse(self, text):
        section = {"code": None, "comment": None}
        while 1:
            code, sep, after = text.partition("/*")

            if code:
                section["code"] = Code(code)

            if (section["comment"] or section["code"]):
                self.content.append(section)
                section = {"code": "", "comment": ""}

            if sep is "" and after is "":
                return

            comment, sep, text = after.partition("*/")

            if comment[0] != "!":
                section["comment"] = Comment(comment)

class Code:
    def __init__(self, codeString):
        self.code = ""
        self.parse(codeString)

    def parse(self, code):
        # Not much to do here
        self.code = code.strip()

    def formatted(self):
        return highlight(self.code, JavascriptLexer(), HtmlFormatter())

class Comment:
    def __init__(self, commentString):
        self.body = ""
        self.tags = []
        self.parse(commentString)

    def parse(self, comment):
        # Remove asterisks from the start of lines
        comment = re.sub("^ *\* ?", "", comment, 0, re.MULTILINE)

        # Grab any JSDoc tags
        matches = re.finditer("(^@\w+.*)", comment, re.MULTILINE)

        for match in matches:
            # Remove the tag
            tag = match.groups()[0]
            comment = comment.replace(tag, "", 1)
            self.tags.append(Tag(tag))

        # Remove newlines from the start and end
        comment = comment.strip()

        # Convert single newlines characters into spaces
        comment = re.sub("(?<!\n)\n(?!\n)", " ", comment, 0, re.MULTILINE)
        self.body = comment

    def formatted(self):
        return self.body

class Tag:
    def __init__(self, tagString):
        self.name = ""
        self.body = ""

        self.parse(tagString)

    def parse(self, tagString):
        parts = tagString.split()
        self.name = parts[0][1:]

        self.body = " ".join(parts[1:])

if __name__ == "__main__":
    OXO()
