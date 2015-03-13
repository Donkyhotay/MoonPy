##############################################################################
#
# Copyright (c) 2006 Zope Corporation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Annotation factory helper

$Id: factory.py 70847 2006-10-20 13:52:45Z ctheune $
"""
import zope.component
import zope.interface
from zope.annotation.interfaces import IAnnotations
import zope.app.container.contained

def factory(factory, key=None):
    """Adapter factory to help create annotations easily.
    """
    # if no key is provided,
    # we'll determine the unique key based on the factory's dotted name
    if key is None:
        key = factory.__module__ + '.' + factory.__name__

    adapts = zope.component.adaptedBy(factory)
    if adapts is None:
        raise TypeError("Missing 'zope.component.adapts' on annotation")

    @zope.component.adapter(list(adapts)[0])
    @zope.interface.implementer(list(zope.component.implementedBy(factory))[0])
    def getAnnotation(context):
        annotations = IAnnotations(context)
        try:
            result = annotations[key]
        except KeyError:
            result = factory()
            annotations[key] = result
        # Containment has to be set up late to allow containment proxies
        # to be applied, if needed. This does not trigger an event and is idempotent
        # if containment is set up already.
        contained_result = zope.app.container.contained.contained(
            result, context, key)
        return contained_result

    # Convention to make adapter introspectable, used by apidoc
    getAnnotation.factory = factory 
    return getAnnotation
