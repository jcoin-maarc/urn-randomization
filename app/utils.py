def __unicode__(self):
        """Give a readable representation of an instance."""
        return "{}".format(self.id)


def __repr__(self):
    """Give a unambiguous representation of an instance."""
    return "<{}#{}>".format(self.__class__.__name__, self.id)
