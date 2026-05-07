// INTENTIONALLY VULNERABLE — AI / training fixture only.
import javax.xml.parsers.DocumentBuilder;
import javax.xml.parsers.DocumentBuilderFactory;
import org.w3c.dom.Document;
import java.io.InputStream;

public class ParseUserXml {
    public Document parse(InputStream in) throws Exception {
        DocumentBuilderFactory dbf = DocumentBuilderFactory.newInstance();
        DocumentBuilder db = dbf.newDocumentBuilder();
        return db.parse(in); // XXE possible if FEATURE_SECURE_PROCESSING disabled
    }
}
